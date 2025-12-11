# parser.py
import re
from utils import PERIOD_TIMES

# 取得 utils 定義的節次標籤列表
PERIOD_LABELS = list(PERIOD_TIMES.keys())

# 星期映射
DAY_MAP = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}

# 節次行號映射補強 (處理 10, 11, 12 轉為 A, B, C 的對應)
# 邏輯：輸入的數字是對應「第幾行」，所以 10 對應 index 9
def get_row_index(row_str):
    try:
        # 嘗試直接轉數字 (針對 "1", "2", "12"...)
        val = int(row_str)
        return val - 1  # 轉為 0-based index
    except ValueError:
        # 如果使用者手動輸入 "A", "B" 等非數字
        map_char = {
            "A": 10, "B": 11, "C": 12, "D": 13,
            "a": 10, "b": 11, "c": 12, "d": 13
        }
        return map_char.get(row_str, -1)

def parse_schedule_text(text):
    """
    將文字代碼解析為 Renderer 可用的二維陣列
    """
    matrix = [["" for _ in range(8)] for _ in range(14)]
    
    # 預填第一欄
    for i, label in enumerate(PERIOD_LABELS):
        if i < 14:
            matrix[i][0] = label

    # Regex 解析
    # 說明：
    # #([一二三四五六日]) : 抓取 # 開頭接星期
    # ([0-9]+|[A-Da-d]) : 抓取行號 (數字或 ABCD)
    # :                 : 冒號分隔
    # ([^#]*)           : 抓取內容直到下一個 # 出現
    pattern = re.compile(r'#([一二三四五六日])([0-9]+|[A-Da-d]):([^#]*)')
    matches = pattern.findall(text)
    
    for day, row_str, content in matches:
        content = content.strip()
        
        col_idx = DAY_MAP.get(day)
        row_idx = get_row_index(row_str)
        
        if col_idx is not None and 0 <= row_idx < 14:
            if matrix[row_idx][col_idx]:
                matrix[row_idx][col_idx] += "\n" + content
            else:
                matrix[row_idx][col_idx] = content

    return matrix