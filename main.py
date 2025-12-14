import customtkinter as ctk
import tkinter as tk  # 必須引入標準 tkinter 來建立 Mac 原生選單
import threading
from tkinter import messagebox, filedialog
from PIL import Image
import os

# --- 引入專案模組 ---
from scraper import SoochowScraper  # 這裡改用真正的爬蟲
from renderer import TimetableRenderer
from parser import parse_schedule_text

# 設定外觀主題
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("東吳課表美化產生器 (M系列優化版)")
        self.geometry("1100x750")
        self.minsize(900, 650)

        # --- Mac 視窗優化 ---
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)

        # --- [關鍵修復] 建立 Mac 原生選單 (讓 Cmd+C/V 可用) ---
        self._create_global_menu()

        # --- 初始化核心模組 ---
        # headless=True 代表在背景執行，不顯示瀏覽器視窗
        # 如果你想看它跑，可以改成 headless=False
        self.scraper = SoochowScraper(headless=True)
        self.renderer = TimetableRenderer()
        self.current_image_path = None
        
        self.default_hint = "#二1:體育... (請在此貼上代碼)"

        # --- 介面佈局 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 左側 Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self.sidebar, width=280)
        self.tabview.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.tab_auto = self.tabview.add("自動抓取")
        self.tab_manual = self.tabview.add("貼上代碼")

        self._init_auto_tab()
        self._init_manual_tab()

        # 右側 Preview Area
        self.preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        # 圖片標籤 (點擊可放大)
        self.img_lbl = ctk.CTkLabel(self.preview_frame, text="請在左側選擇模式並產生課表\n(圖片產生後將完整顯示於此)", cursor="arrow")
        self.img_lbl.grid(row=0, column=0, sticky="nsew")
        self.img_lbl.bind("<Button-1>", self.open_zoom_window)

        # 下載按鈕
        self.btn_down = ctk.CTkButton(self.preview_frame, text="下載 JPG", command=self.download, state="disabled")
        self.btn_down.grid(row=1, column=0, sticky="e", pady=(10,0))

        self.status_lbl = ctk.CTkLabel(self.sidebar, text="就緒", text_color="gray")
        self.status_lbl.grid(row=1, column=0, pady=10)

    # ==========================================
    # [核心修復] 建立 Mac 全域選單
    # ==========================================
    def _create_global_menu(self):
        menubar = tk.Menu(self)
        edit_menu = tk.Menu(menubar, tearoff=0)
        
        edit_menu.add_command(label="剪下 (Cut)", accelerator="Cmd+X", 
                              command=lambda: self.focus_get().event_generate("<<Cut>>"))
        edit_menu.add_command(label="複製 (Copy)", accelerator="Cmd+C", 
                              command=lambda: self.focus_get().event_generate("<<Copy>>"))
        edit_menu.add_command(label="貼上 (Paste)", accelerator="Cmd+V", 
                              command=lambda: self.focus_get().event_generate("<<Paste>>"))
        edit_menu.add_command(label="全選 (Select All)", accelerator="Cmd+A", 
                              command=lambda: self.focus_get().event_generate("<<SelectAll>>"))
        
        menubar.add_cascade(label="編輯", menu=edit_menu)
        self.config(menu=menubar)

    def _init_auto_tab(self):
        ctk.CTkLabel(self.tab_auto, text="學校系統登入", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=20)
        self.user_entry = ctk.CTkEntry(self.tab_auto, placeholder_text="學號 / 帳號")
        self.user_entry.pack(pady=10, padx=10, fill="x")
        self.pass_entry = ctk.CTkEntry(self.tab_auto, placeholder_text="密碼", show="*")
        self.pass_entry.pack(pady=10, padx=10, fill="x")
        
        self.btn_run_auto = ctk.CTkButton(self.tab_auto, text="登入並製作", command=self.start_auto_thread)
        self.btn_run_auto.pack(pady=20, padx=10, fill="x")

    def _init_manual_tab(self):
        title_frame = ctk.CTkFrame(self.tab_manual, fg_color="transparent")
        title_frame.pack(pady=(20, 5), fill="x", padx=10)
        ctk.CTkLabel(title_frame, text="貼上文字代碼", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        
        self.btn_paste = ctk.CTkButton(title_frame, text="📋 貼上", width=60, height=24, 
                                     fg_color="#607D8B", hover_color="#455A64",
                                     command=self.paste_from_clipboard)
        self.btn_paste.pack(side="right")

        self.text_input = ctk.CTkTextbox(self.tab_manual, height=300)
        self.text_input.pack(pady=10, padx=10, fill="both", expand=True)
        self.text_input.insert("0.0", self.default_hint)
        
        self.btn_run_manual = ctk.CTkButton(self.tab_manual, text="解析並製作", command=self.start_manual_thread, fg_color="#2E8B57", hover_color="#228B22")
        self.btn_run_manual.pack(pady=20, padx=10, fill="x")

    def paste_from_clipboard(self):
        try:
            content = self.clipboard_get()
            if content:
                self.text_input.delete("0.0", "end")
                self.text_input.insert("0.0", content)
        except Exception: 
            pass

    # --- 執行緒處理 ---
    def start_auto_thread(self):
        threading.Thread(target=self.process_auto, daemon=True).start()

    def start_manual_thread(self):
        threading.Thread(target=self.process_manual, daemon=True).start()

    # --- 核心邏輯: 自動抓取 ---
    def process_auto(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        if not user or not pwd:
            messagebox.showwarning("提示", "請輸入帳號密碼")
            return
        
        self._set_loading(True, "正在連線學校系統...")
        try:
            # 呼叫 Scraper 進行登入與爬取
            # 這一步比較久，所以狀態文字會變
            self.status_lbl.configure(text="登入中...請稍候")
            
            # 這裡會回傳一個 14x8 的二維陣列
            raw_data = self.scraper.get_timetable_data(user, pwd)
            
            if not raw_data:
                raise Exception("抓取失敗或無資料")

            self._render_and_show(raw_data)
            
        except Exception as e:
            self._handle_error(e)
        finally:
            self._set_loading(False)

    # --- 核心邏輯: 手動貼上 ---
    def process_manual(self):
        text_code = self.text_input.get("1.0", "end").strip()
        if not text_code or text_code == self.default_hint:
            messagebox.showwarning("提示", "請貼上有效的課表代碼")
            return
        self._set_loading(True, "解析渲染中...")
        threading.Thread(target=self._run_manual_process, args=(text_code,), daemon=True).start()

    def _run_manual_process(self, text_code):
        try:
            matrix_data = parse_schedule_text(text_code)
            
            # 簡單檢查是否有資料
            has_data = False
            for row in matrix_data:
                for col_idx, cell in enumerate(row):
                    if col_idx > 0 and cell: 
                        has_data = True
                        break
                if has_data: break
            
            if not has_data:
                self.after(0, lambda: messagebox.showerror("解析失敗", "無法識別代碼格式"))
                self._set_loading(False)
                return
                
            self._render_and_show(matrix_data)
        except Exception as e:
            self._handle_error(e)
            self._set_loading(False)

    def _render_and_show(self, data):
        self.status_lbl.configure(text="正在生成高畫質圖片...")
        try:
            img_path = self.renderer.render_to_jpg(data)
            self.current_image_path = img_path
            self.after(0, self.show_image, img_path)
            self.status_lbl.configure(text="完成", text_color="green")
        except Exception as e:
            self._handle_error(e)

    def _set_loading(self, is_loading, msg=""):
        state = "disabled" if is_loading else "normal"
        # 為了避免在非主執行緒操作 GUI 報錯，建議用 after 或是簡單配置
        # 這裡用 configure 是安全的，因為 customtkinter 有處理，但標準 tk 需小心
        self.btn_run_auto.configure(state=state)
        self.btn_run_manual.configure(state=state)
        self.status_lbl.configure(text=msg, text_color="orange" if is_loading else "gray")

    def _handle_error(self, e):
        print(f"Error: {e}")
        self.after(0, lambda: self.status_lbl.configure(text="發生錯誤", text_color="red"))
        self.after(0, lambda: messagebox.showerror("錯誤", str(e)))

    def show_image(self, path):
        if not os.path.exists(path): return
        pil_img = Image.open(path)
        
        # 預覽縮放邏輯 (保持比例)
        MAX_W, MAX_H = 750, 580
        w_ratio = MAX_W / pil_img.width
        h_ratio = MAX_H / pil_img.height
        scale = min(w_ratio, h_ratio, 1.0)
        new_w = int(pil_img.width * scale)
        new_h = int(pil_img.height * scale)
        
        ctk_img = ctk.CTkImage(light_image=pil_img, size=(new_w, new_h))
        self.img_lbl.configure(image=ctk_img, text="", cursor="pointinghand")
        self.btn_down.configure(state="normal")
        self.status_lbl.configure(text="完成！點擊圖片可放大檢視", text_color="green")

    def open_zoom_window(self, event=None):
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            return

        top = ctk.CTkToplevel(self)
        top.title("課表放大檢視")
        top.geometry("1000x800")
        
        top.lift()
        top.attributes('-topmost', True)
        top.after_idle(top.attributes, '-topmost', False)

        scroll_frame = ctk.CTkScrollableFrame(top, orientation="vertical")
        scroll_frame.pack(fill="both", expand=True)

        pil_img = Image.open(self.current_image_path)
        # 這裡顯示原圖大小
        full_ctk_img = ctk.CTkImage(light_image=pil_img, size=pil_img.size)
        
        lbl_zoom = ctk.CTkLabel(scroll_frame, text="", image=full_ctk_img)
        lbl_zoom.pack()

    def download(self):
        if not self.current_image_path: return
        path = filedialog.asksaveasfilename(
            defaultextension=".jpg", 
            filetypes=[("JPG", "*.jpg")], 
            initialfile="我的課表.jpg"
        )
        if path:
            import shutil
            shutil.copy(self.current_image_path, path)
            messagebox.showinfo("成功", f"檔案已儲存至: {path}")

if __name__ == "__main__":
    app = App()
    app.mainloop()