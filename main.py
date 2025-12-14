import customtkinter as ctk
import tkinter as tk  # 必須引入標準 tkinter 來建立 Mac 原生選單
import threading
from tkinter import messagebox, filedialog
from PIL import Image
import os

# --- 引入專案模組 ---
from scraper import SoochowScraper
from renderer import TimetableRenderer
from parser import parse_schedule_text
import config  # 引入設定檔模組

# 設定外觀主題
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- 1. 設定視窗標題與大小 ---
        self.title("東吳課表魔法貓貓")
        self.geometry("1100x750")
        self.minsize(900, 650)

        # --- Mac 視窗優化 ---
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)

        # --- 建立 Mac 原生選單 ---
        self._create_global_menu()

        # --- 初始化核心模組 ---
        self.scraper = SoochowScraper(headless=True)
        self.renderer = TimetableRenderer()
        self.current_image_path = None
        self.current_pil_image = None  # [新增] 用來暫存原始圖片物件，方便縮放
        self.default_hint = "#二1:體育... (請在此貼上代碼)"

        # --- [載入圖片] ---
        try:
            image_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "cat_logo.png")
            self.logo_image = ctk.CTkImage(
                light_image=Image.open(image_path),
                dark_image=Image.open(image_path),
                size=(120, 120)
            )
            # 設定 App Icon (macOS)
            icon_img = tk.PhotoImage(file=image_path)
            self.iconphoto(True, icon_img)
        except Exception as e:
            print(f"提示: 找不到圖片或讀取失敗 ({e})，將略過圖片顯示")
            self.logo_image = None

        # --- [主介面佈局] ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. 左側 Sidebar
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Sidebar 內容 (使用 pack)
        if self.logo_image:
            self.logo_label = ctk.CTkLabel(self.sidebar, text="", image=self.logo_image)
            self.logo_label.pack(pady=(30, 10))

        # 分頁選單
        self.tabview = ctk.CTkTabview(self.sidebar, width=280)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_auto = self.tabview.add("自動抓取")
        self.tab_manual = self.tabview.add("貼上代碼")

        self._init_auto_tab()
        self._init_manual_tab()

        # 狀態標籤
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="就緒", text_color="gray")
        self.status_lbl.pack(side="bottom", pady=20)


        # 2. 右側 Preview Area
        self.preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        # [修改] 這裡把 padx, pady 改小 (原本是 20)，讓空間更大
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        # [新增] 綁定視窗大小改變事件，觸發圖片重繪
        self.preview_frame.bind("<Configure>", self.resize_image_event)

        # 圖片標籤
        self.img_lbl = ctk.CTkLabel(self.preview_frame, text="請在左側選擇模式並產生課表\n(圖片產生後將完整顯示於此)", cursor="arrow")
        self.img_lbl.grid(row=0, column=0, sticky="nsew")
        self.img_lbl.bind("<Button-1>", self.open_zoom_window)

        # 下載按鈕 (放在右下角)
        self.btn_down = ctk.CTkButton(self.preview_frame, text="下載 JPG", command=self.download, state="disabled")
        self.btn_down.grid(row=1, column=0, sticky="se", pady=10, padx=10) # 改用 sticky="se" 固定在右下角

    # ==========================================
    # 以下邏輯保持不變
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
        
        self.remember_var = ctk.BooleanVar(value=False)
        self.chk_remember = ctk.CTkCheckBox(self.tab_auto, text="記住帳號密碼", variable=self.remember_var)
        self.chk_remember.pack(pady=5, padx=10, anchor="w")
        
        self._load_saved_credentials()

        self.btn_run_auto = ctk.CTkButton(self.tab_auto, text="登入並製作", command=self.start_auto_thread)
        self.btn_run_auto.pack(pady=20, padx=10, fill="x")

    def _load_saved_credentials(self):
        saved_data = config.load_config()
        if saved_data.get("remember_me", False):
            self.remember_var.set(True)
            if "username" in saved_data:
                self.user_entry.insert(0, saved_data["username"])
            if "password" in saved_data:
                self.pass_entry.insert(0, saved_data["password"])

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

    def start_auto_thread(self):
        threading.Thread(target=self.process_auto, daemon=True).start()

    def start_manual_thread(self):
        threading.Thread(target=self.process_manual, daemon=True).start()

    def process_auto(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        remember = self.remember_var.get()

        if not user or not pwd:
            messagebox.showwarning("提示", "請輸入帳號密碼")
            return
        
        config.save_config(user, pwd, remember)
        
        self._set_loading(True, "正在連線學校系統...")
        try:
            self.status_lbl.configure(text="登入中...請稍候")
            raw_data = self.scraper.get_timetable_data(user, pwd)
            if not raw_data:
                raise Exception("抓取失敗或無資料")
            self._render_and_show(raw_data)
        except Exception as e:
            self._handle_error(e)
        finally:
            self._set_loading(False)

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
            # 1. 產生圖片並存檔
            img_path = self.renderer.render_to_jpg(data)
            self.current_image_path = img_path
            
            # 2. [新增] 將圖片讀入記憶體，設為 current_pil_image 供縮放使用
            self.current_pil_image = Image.open(img_path)
            
            # 3. 呼叫更新顯示
            self.after(0, lambda: self.resize_image_event(None))
            
            self.status_lbl.configure(text="完成", text_color="green")
        except Exception as e:
            self._handle_error(e)

    # [新增] 動態縮放圖片的事件處理函式
    def resize_image_event(self, event):
        if not self.current_pil_image:
            return

        # 取得當前 Preview Frame 的寬高
        frame_width = self.preview_frame.winfo_width()
        frame_height = self.preview_frame.winfo_height()

        # 扣除一些邊距與下方按鈕的空間
        # 如果不扣除，圖片可能會稍微超出視窗或蓋住按鈕
        target_w = frame_width - 10 
        target_h = frame_height - 60 

        # 避免視窗剛啟動時數值過小導致錯誤
        if target_w < 50 or target_h < 50:
            return

        # 計算等比例縮放
        img_w, img_h = self.current_pil_image.size
        ratio = min(target_w / img_w, target_h / img_h)
        
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        # 建立 CustomTkinter 圖片物件
        ctk_img = ctk.CTkImage(light_image=self.current_pil_image, size=(new_w, new_h))
        
        # 更新 Label
        self.img_lbl.configure(image=ctk_img, text="")
        
        # 啟用下載按鈕
        self.btn_down.configure(state="normal")

    def _set_loading(self, is_loading, msg=""):
        state = "disabled" if is_loading else "normal"
        self.btn_run_auto.configure(state=state)
        self.btn_run_manual.configure(state=state)
        self.status_lbl.configure(text=msg, text_color="orange" if is_loading else "gray")

    def _handle_error(self, e):
        print(f"Error: {e}")
        self.after(0, lambda: self.status_lbl.configure(text="發生錯誤", text_color="red"))
        self.after(0, lambda: messagebox.showerror("錯誤", str(e)))

    def show_image(self, path):
        # 此函式目前主要被 _render_and_show 取代，但保留兼容性
        if not os.path.exists(path): return
        self.current_image_path = path
        self.current_pil_image = Image.open(path)
        self.resize_image_event(None)

    def open_zoom_window(self, event=None):
        if not self.current_image_path or not os.path.exists(self.current_image_path):
            return

        # 1. 建立獨立視窗
        top = ctk.CTkToplevel(self)
        top.title("課表詳細檢視")
        top.geometry("900x800") # 設定一個適合閱讀的高度
        
        # 讓視窗置頂一下確保浮現
        top.lift()
        top.attributes('-topmost', True)
        top.after_idle(top.attributes, '-topmost', False)

        # 2. 頂部工具列 (新增功能按鈕)
        toolbar = ctk.CTkFrame(top, height=40)
        toolbar.pack(fill="x", padx=10, pady=5)

        # 加入 "用系統預覽程式開啟" 按鈕 (Mac 神器)
        btn_preview = ctk.CTkButton(
            toolbar, 
            text="🔍 用 Mac 預覽程式開啟 (推薦)", 
            command=self.open_in_system_viewer,
            fg_color="#4B4B4B", hover_color="#666666", width=200
        )
        btn_preview.pack(side="right", padx=5)

        ctk.CTkLabel(toolbar, text="💡 提示：圖片已自動縮放至適合寬度，請上下捲動檢視。").pack(side="left", padx=5)

        # 3. 內容捲動區
        scroll_frame = ctk.CTkScrollableFrame(top, orientation="vertical")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 4. 圖片處理 (關鍵優化：符合寬度)
        pil_img = Image.open(self.current_image_path)
        
        # 設定目標顯示寬度 (扣除捲軸寬度，大約 850px 比較剛好)
        display_width = 860 
        
        # 計算等比例高度
        w_percent = (display_width / float(pil_img.size[0]))
        h_size = int((float(pil_img.size[1]) * float(w_percent)))
        
        # 縮放圖片 (使用 LANCZOS 演算法保持文字清晰)
        resized_img = pil_img.resize((display_width, h_size), Image.Resampling.LANCZOS)
        
        ctk_img = ctk.CTkImage(light_image=resized_img, size=(display_width, h_size))
        
        # 顯示圖片
        lbl_zoom = ctk.CTkLabel(scroll_frame, text="", image=ctk_img)
        lbl_zoom.pack(pady=10)

        # 讓滑鼠滾輪在圖片上也能捲動 (優化體驗)
        # 這裡綁定的是 scroll_frame 的 canvas 捲動事件
        # 注意：CustomTkinter 的 ScrollableFrame 內部機制較複雜，通常滑鼠放在 scrollbar 區域滾動即可

    def open_in_system_viewer(self):
        """直接呼叫 macOS 的預覽程式開啟圖片"""
        if not self.current_image_path: return
        try:
            import subprocess
            # macOS 的 'open' 指令
            subprocess.run(["open", self.current_image_path])
        except Exception as e:
            print(f"開啟預覽失敗: {e}")
            messagebox.showerror("錯誤", "無法開啟系統預覽程式")

    def download(self):
        if not self.current_image_path: return
        path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPG", "*.jpg")], initialfile="我的課表.jpg")
        if path:
            import shutil
            shutil.copy(self.current_image_path, path)
            messagebox.showinfo("成功", f"檔案已儲存至: {path}")

if __name__ == "__main__":
    app = App()
    app.mainloop()