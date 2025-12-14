from playwright.sync_api import sync_playwright
import time

class SoochowScraper:
    def __init__(self, headless=False):
        """
        初始化爬蟲
        :param headless: 是否隱藏瀏覽器視窗 (測試時建議設為 False)
        """
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        # 啟動 Chrome 瀏覽器 (channel="chrome" 使用本機 Chrome，若無可移除該參數)
        self.browser = self.playwright.chromium.launch(headless=self.headless, channel="chrome")
        # 建立獨立的瀏覽器環境 (Context)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self, username, password):
        """
        執行登入動作
        回傳: True (成功), False (失敗)
        """
        login_url = "https://web.sys.scu.edu.tw/logins.asp"
        print(f"[*] 正在前往登入頁面: {login_url}")
        
        try:
            self.page.goto(login_url)
            
            print("[*] 正在輸入帳號密碼...")
            
            # 等待並填寫帳號 (name="id")
            self.page.wait_for_selector("input[name='id']", timeout=5000)
            self.page.fill("input[name='id']", username)
            
            # 填寫密碼 (name="passwd")
            self.page.fill("input[name='passwd']", password)
            
            print("[*] 嘗試登入...")
            
            # 模擬按下 Enter 鍵登入 (觸發 JS 事件)
            self.page.press("input[name='passwd']", "Enter")
            
            # (備用) 如果按 Enter 無效，可以解開下方註解改用點擊按鈕
            # self.page.click("#btnLogin")

            print("[*] 等待登入驗證 (約需 3-5 秒)...")
            self.page.wait_for_timeout(5000) 

            # 驗證 Cookie (檢查 login0 是否為 TRUE)
            cookies = self.context.cookies()
            is_logged_in = False
            for cookie in cookies:
                if cookie['name'] == 'login0' and cookie['value'] == 'TRUE':
                    is_logged_in = True
                    print(f"[debug] 登入成功！Cookie login0={cookie['value']}")
                    break
            
            return is_logged_in

        except Exception as e:
            print(f"[!] 登入失敗: {e}")
            return False

    def get_raw_timetable(self):
        """
        進入課表頁面 -> 點擊查詢 -> 回傳 HTML
        """
        target_url = "https://web.sys.scu.edu.tw/coursetbl00.asp"
        print(f"[*] 正在前往課表頁面: {target_url}")
        
        try:
            self.page.goto(target_url)
            
            # 1. 檢查是否被踢回登入頁
            if "logins.asp" in self.page.url:
                print("[!] 頁面被導回 logins.asp，可能登入失效")
                return None

            # 2. 點擊查詢按鈕
            print("[*] 正在點擊「查詢」按鈕...")
            try:
                # 使用 expect_navigation 等待點擊後造成的頁面刷新
                with self.page.expect_navigation(timeout=10000):
                    # 定位 value 包含 "Query" 或 "查詢" 的 submit 按鈕
                    # 或是直接用 input[type='submit']
                    self.page.click("input[type='submit']")
                
                print("[*] 頁面已刷新，等待內容完整載入...")
                
                # 等待網路閒置，確保表格資料已下載
                self.page.wait_for_load_state("networkidle")
                
            except Exception as e:
                print(f"[!] 點擊查詢或等待刷新時發生狀況 (可能是因為沒有頁面跳轉，僅局部更新?): {e}")
                # 為了保險，再強制等個 2 秒
                self.page.wait_for_timeout(2000)

            # 3. 抓取內容
            content = self.page.content()
            
            # 簡單驗證關鍵字
            if "衝堂" in content or "節次" in content or "星期一" in content:
                print("[V] HTML 中發現課表相關關鍵字。")
            else:
                print("[?] 警告：HTML 中未發現常見課表關鍵字，請檢查輸出的 HTML 檔。")

            return content

        except Exception as e:
            print(f"[!] 抓取課表失敗: {e}")
            return None