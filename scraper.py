from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

class SoochowScraper:
    def __init__(self, headless=True):
        self.headless = headless

    def get_timetable_data(self, username, password):
        """
        GUI 呼叫的主入口：包含 啟動瀏覽器 -> 登入 -> 抓取 -> 解析 -> 關閉
        回傳: 二維陣列 (Matrix)
        """
        data = []
        with sync_playwright() as p:
            # 啟動瀏覽器
            browser = p.chromium.launch(headless=self.headless, channel="chrome")
            context = browser.new_context()
            page = context.new_page()

            try:
                # 1. 登入
                if not self._login_step(page, context, username, password):
                    raise Exception("登入失敗，請檢查帳號密碼")

                # 2. 抓取 HTML
                html_content = self._fetch_html_step(page)
                if not html_content:
                    raise Exception("抓取課表失敗")

                # 3. 解析 HTML
                data = self._parse_html(html_content)

            finally:
                browser.close()
        
        return data

    def _login_step(self, page, context, username, password):
        """內部步驟：處理登入"""
        print(f"[*] 前往登入頁面...")
        page.goto("https://web.sys.scu.edu.tw/logins.asp")
        
        try:
            page.wait_for_selector("input[name='id']", timeout=5000)
            page.fill("input[name='id']", username)
            page.fill("input[name='passwd']", password)
            page.press("input[name='passwd']", "Enter")
            
            # 等待登入 Cookie
            page.wait_for_timeout(3000)
            cookies = context.cookies()
            for cookie in cookies:
                if cookie['name'] == 'login0' and cookie['value'] == 'TRUE':
                    return True
            return False
        except Exception as e:
            print(f"[Login Error] {e}")
            return False

    def _fetch_html_step(self, page):
        """內部步驟：點擊查詢並取得 HTML"""
        print(f"[*] 前往課表頁面...")
        page.goto("https://web.sys.scu.edu.tw/coursetbl00.asp")
        
        if "logins.asp" in page.url:
            return None

        try:
            # 點擊查詢按鈕 (Submit)
            with page.expect_navigation(timeout=15000):
                page.click("input[type='submit']")
            
            page.wait_for_load_state("networkidle")
            return page.content()
        except Exception as e:
            print(f"[Fetch Error] {e}")
            return None

    def _parse_html(self, html_content):
        """
        解析 HTML 為 14x8 的二維陣列
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        data = []
        
        # 尋找表格
        table = soup.find('table')
        if not table:
            raise Exception("找不到課表表格")

        rows = table.find_all('tr')
        
        # 跳過第一列 (表頭: 節次、星期一...)
        # 從第二列開始抓 (節次 1 ~ D)
        for tr in rows[1:]:
            cells = tr.find_all('td')
            if not cells: continue

            row_data = []
            
            # 第一格是節次 (例如 "1", "A")
            # 為了對齊 GUI，我們可以直接讀取文字，或者強制依照順序填入
            period_label = cells[0].get_text(strip=True)
            row_data.append(period_label)

            # 後面 7 格是星期一~日
            for td in cells[1:]:
                # 使用 separator="\n" 讓單雙週課程可以換行顯示
                # strip=True 會自動去除前後空白
                cell_text = td.get_text(separator="\n", strip=True)
                row_data.append(cell_text)

            data.append(row_data)

        # 簡單驗證：應該要有 14 列 (1,2,3,4,E,5,6,7,8,9,A,B,C,D)
        if len(data) < 10: 
            print(f"[Warning] 解析出的列數只有 {len(data)} 列，可能不完整")

        return data