# scraper.py
import time
from playwright.sync_api import sync_playwright

class MockScraper:
    def get_timetable_data(self, username, password):
        time.sleep(1) # 模擬
        # 模擬資料
        return [
            ["１", "國文", "", "英文", "", "", "", ""],
            ["２", "國文", "", "英文", "體育", "", "", ""],
            ["３", "", "微積分", "", "微積分", "", "", ""],
            ["４", "", "微積分", "", "微積分", "", "", ""],
            ["Ｅ", "", "", "", "", "", "", ""],
            ["５", "物理", "", "程式設計", "", "通識", "", ""],
            ["６", "物理", "", "程式設計", "", "通識", "", ""],
        ]

# 真正實作時，Playwright 寫法範例：
class RealScraper:
    def get_timetable_data(self, username, password):
        data = []
        with sync_playwright() as p:
            # mac 上 headless=False 方便除錯，正式跑改 True
            browser = p.chromium.launch(headless=True) 
            page = browser.new_page()
            # page.goto("學校網址")
            # page.fill("#username", username)
            # ... 爬蟲邏輯 ...
            browser.close()
        return data