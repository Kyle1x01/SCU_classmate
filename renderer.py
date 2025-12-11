import os
from playwright.sync_api import sync_playwright
from utils import PERIOD_TIMES

# 取得 utils 定義的節次標籤列表
PERIOD_LABELS = list(PERIOD_TIMES.keys())
HEADERS = ["節次", "一", "二", "三", "四", "五", "六", "日"]

class TimetableRenderer:
    def __init__(self):
        # 設定輸出目錄
        self.output_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_html_content(self, processed_data):
        # HTML/CSS 樣式保持不變，因為我們是透過瀏覽器縮放來提升畫質
        css_style = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; padding: 40px 20px; margin: 0;}
            .outer-container { display: flex; flex-direction: column; align-items: center; background-color: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
            .grid-container { display: grid; grid-template-columns: repeat(8, 1fr); gap: 12px; max-width: 900px; }
            .header-cell { background: #8B0000; color: white; text-align: center; padding: 15px 10px; font-weight: bold; border-radius: 8px; font-size: 16px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
            .grid-cell { background: #f8f9fa; color: #333; padding: 8px; display: flex; align-items: center; justify-content: center; text-align: center; border: 1px solid #e9ecef; font-weight: 600; min-width: 85px; min-height: 75px; font-size: 13px; border-radius: 8px; white-space: pre-wrap; transition: all 0.2s ease; }
            .period-cell { background: #ffebee; flex-direction: column; color: #c62828; border-color: #ffcdd2; font-size: 14px;}
            .note { text-align: center; font-size: 14px; margin-top: 25px; color: #777; font-weight: 500; width: 100%; }
        </style>
        """
        
        cells_html = ""
        for header in HEADERS:
            cells_html += f'<div class="header-cell">{header}</div>'
        
        for row_idx in range(14):
            row_data = processed_data[row_idx]
            for col_idx in range(8):
                cell_text = row_data[col_idx]
                extra_class = "period-cell" if col_idx == 0 else ""
                display_text = cell_text if cell_text else "&nbsp;"
                cells_html += f'<div class="grid-cell {extra_class}">{display_text}</div>'
                
        full_html = f"""
        <!DOCTYPE html>
        <html>
            <head>
                <meta charset="utf-8">
                {css_style}
            </head>
            <body>
                <div class="outer-container">
                    <div class="grid-container">{cells_html}</div>
                    <div class="note">Designed by Python Timetable Generator</div>
                </div>
            </body>
        </html>
        """
        return full_html

    def render_to_jpg(self, matrix_data, filename="timetable.jpg"):
        html_content = self.generate_html_content(matrix_data)
        output_path = os.path.join(self.output_dir, filename)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            
            # --- [畫質提升關鍵設定] ---
            # device_scale_factor: 設定為 3 (類似 iPhone/Mac Retina 螢幕)，
            # 這會讓 1px 的 CSS 寬度變成 3px 的物理像素，字體會變得超級清晰。
            page = browser.new_page(
                viewport={"width": 1200, "height": 1200},
                device_scale_factor=3  
            )
            
            page.set_content(html_content)
            page.wait_for_timeout(500)
            
            # 使用 full_page=True 確保完整截圖
            # quality=100 設定為最高品質 JPEG
            page.screenshot(path=output_path, full_page=True, type="jpeg", quality=100)
            
            browser.close()

        print(f"圖片已生成: {output_path}")
        return output_path