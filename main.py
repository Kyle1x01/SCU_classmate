# main.py
import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog
from PIL import Image
import os

from scraper import MockScraper
from renderer import TimetableRenderer

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("課表美化產生器 (Mac版)")
        self.geometry("1000x700")

        # [Mac 優化] 確保視窗在最上層，避免被 Terminal 蓋住
        self.lift()
        self.attributes('-topmost',True)
        self.after_idle(self.attributes,'-topmost',False)

        # 核心模組
        self.scraper = MockScraper()
        self.renderer = TimetableRenderer()
        self.current_image_path = None

        # --- 介面佈局 (Grid) ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="課表抓取", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(30,10))
        
        self.user_entry = ctk.CTkEntry(self.sidebar, placeholder_text="學號")
        self.user_entry.pack(pady=10, padx=20, fill="x")
        
        self.pass_entry = ctk.CTkEntry(self.sidebar, placeholder_text="密碼", show="*")
        self.pass_entry.pack(pady=10, padx=20, fill="x")

        self.btn_run = ctk.CTkButton(self.sidebar, text="開始製作", command=self.start_thread)
        self.btn_run.pack(pady=20, padx=20, fill="x")
        
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="就緒", text_color="gray")
        self.status_lbl.pack(pady=10, side="bottom")

        # Preview Area
        self.preview_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.preview_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.preview_frame.grid_columnconfigure(0, weight=1)
        self.preview_frame.grid_rowconfigure(0, weight=1)

        self.img_lbl = ctk.CTkLabel(self.preview_frame, text="預覽區域")
        self.img_lbl.grid(row=0, column=0)

        self.btn_down = ctk.CTkButton(self.preview_frame, text="下載 JPG", command=self.download, state="disabled")
        self.btn_down.grid(row=1, column=0, sticky="e", pady=10)

    def start_thread(self):
        threading.Thread(target=self.process, daemon=True).start()

    def process(self):
        user = self.user_entry.get()
        pwd = self.pass_entry.get()
        if not user or not pwd:
            return # 簡單擋一下
        
        self.btn_run.configure(state="disabled")
        self.status_lbl.configure(text="爬取中...")
        
        try:
            raw_data = self.scraper.get_timetable_data(user, pwd)
            self.status_lbl.configure(text="渲染中...")
            
            img_path = self.renderer.render_to_jpg(raw_data)
            self.current_image_path = img_path
            
            self.after(0, self.show_image, img_path)
            self.status_lbl.configure(text="完成", text_color="green")
            self.btn_down.configure(state="normal")
        except Exception as e:
            print(e)
            self.status_lbl.configure(text="錯誤", text_color="red")
        finally:
            self.btn_run.configure(state="normal")

    def show_image(self, path):
        pil_img = Image.open(path)
        # 縮放顯示
        h_ratio = 600 / pil_img.height
        new_size = (int(pil_img.width * h_ratio), 600)
        
        ctk_img = ctk.CTkImage(light_image=pil_img, size=new_size)
        self.img_lbl.configure(image=ctk_img, text="")

    def download(self):
        if not self.current_image_path: return
        path = filedialog.asksaveasfilename(defaultextension=".jpg", filetypes=[("JPG", "*.jpg")])
        if path:
            import shutil
            shutil.copy(self.current_image_path, path)

if __name__ == "__main__":
    app = App()
    app.mainloop()