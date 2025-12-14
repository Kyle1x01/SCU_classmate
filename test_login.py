from scraper import SoochowScraper
import getpass # 用來隱藏輸入的密碼

def main():
    print("=== 東吳課表爬蟲測試模組 ===")
    user = input("請輸入學號: ")
    # getpass 可以讓密碼輸入時不顯示在螢幕上
    pwd = getpass.getpass("請輸入密碼 (輸入時不會顯示): ")

    # headless=False 會彈出瀏覽器視窗，讓你親眼看到它在幹嘛
    with SoochowScraper(headless=False) as scraper:
        success = scraper.login(user, pwd)
        
        if success:
            print("\n[V] 登入成功！檢測到 login0 Cookie。")
            
            # 嘗試抓取課表頁面
            html = scraper.get_raw_timetable()
            if html:
                print(f"[V] 成功取得課表頁面 HTML (長度: {len(html)})")
                
                # 簡單驗證有沒有抓到課表關鍵字
                if "課表" in html or "節次" in html:
                    print("[V] HTML 內容看起來包含課表資訊。")
                    
                    # 測試：將抓到的 HTML 存檔，你可以打開來檢查
                    with open("debug_timetable.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    print("[*] 已將原始 HTML 存為 'debug_timetable.html' 供檢查")
                else:
                    print("[?] HTML 內容可能不正確，請檢查 debug_timetable.html")
            else:
                print("[X] 抓取課表頁面失敗")
        else:
            print("\n[X] 登入失敗。")
            print("可能原因：")
            print("1. 帳號密碼錯誤")
            print("2. 網頁載入太慢 (可調整 wait_for_timeout)")
            print("3. 輸入框的 Selector 不對 (需要檢查網頁原始碼)")
            
            # 暫停一下讓你看瀏覽器畫面，按 Enter 後關閉
            input("\n按 Enter 關閉瀏覽器...")

if __name__ == "__main__":
    main()