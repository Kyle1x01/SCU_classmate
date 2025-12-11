import re
import pandas as pd

# 原始輸入資料
raw_text = """
#二1:體育－羽球基本技術 B306 　王家閔 #二2:體育－羽球基本技術 B306 　王家閔 #一3:德行取向服務學習實踐類別四 D0407　范綱華 #二3:資料產品開發實務 H313 　葉向原 #三3:機率與統計 B608 　李家萱 #五3:英文（二）４３組初 G203 　鍾環如 #一4:德行取向服務學習實踐類別四 D0407　范綱華 #二4:資料產品開發實務 H313 　葉向原 #三4:機率與統計 B608 　李家萱 #五4:英文（二）４３組初 G203 　鍾環如 #一6:資料產品開發實務 H303 單葉向原 #二6:機率與統計輔導 H110 單    機率與統計 B608 雙李家萱 #五6:互動科技遠距教學 H108 　吳政隆 #一7:資料產品開發實務 H303 單葉向原 #二7:機率與統計輔導 H110 單    機率與統計 B608 雙李家萱 #五7:互動科技遠距教學 H108 　吳政隆 #四8:資料分析軟體 B707 　鄭江宇 #四9:資料分析軟體 B707 　鄭江宇 #四10:資料分析軟體 B707 　鄭江宇 #一11:中華民國憲法 1401 　滕孟豪 #一12:中華民國憲法 1401 　滕孟豪
"""

# 顯示用的節次標籤 (對應我們生成的表格列)
# 索引: 0=1, 1=2, 2=3, 3=4, 4=E, 5=5, 6=6 ...
PERIOD_LABELS = ["１", "２", "３", "４", "Ｅ", "５", "６", "７", "８", "９", "Ａ", "Ｂ", "Ｃ", "Ｄ"]

# 星期映射
DAY_MAP = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "日": 7}

def parse_schedule(text):
    # 初始化一個 14列 x 8行 的空矩陣
    matrix = [["" for _ in range(8)] for _ in range(14)]
    
    # 填入第一欄 (節次標籤)
    for i, label in enumerate(PERIOD_LABELS):
        matrix[i][0] = label

    # 解析 Regex
    pattern = re.compile(r'#([一二三四五六日])(\w+):([^#]*)')
    matches = pattern.findall(text)
    
    for day, row_num_str, content in matches:
        content = content.strip()
        
        # 取得星期欄位索引
        col_idx = DAY_MAP.get(day)
        
        # --- 關鍵修正 ---
        # 輸入的數字其實是「表格行號」。
        # 因為表格行號從 1 開始，而我們的 matrix 索引從 0 開始。
        # 且表格結構 (1,2,3,4,E,5,6...) 與我們的 matrix 結構完全一致。
        # 所以直接將「輸入數字 - 1」就是正確的 matrix 列索引。
        try:
            row_idx = int(row_num_str) - 1
        except ValueError:
            print(f"無法解析的行號: {row_num_str}")
            continue
            
        # 安全檢查：確保索引在範圍內 (0-13)
        if col_idx is not None and 0 <= row_idx < 14:
            if matrix[row_idx][col_idx]:
                matrix[row_idx][col_idx] += "\n" + content
            else:
                matrix[row_idx][col_idx] = content
        else:
            print(f"索引超出範圍或錯誤: {day}{row_num_str}")

    return matrix

# 執行與驗證
parsed_data = parse_schedule(raw_text)
df = pd.DataFrame(parsed_data, columns=["節次", "一", "二", "三", "四", "五", "六", "日"])

# 設定顯示參數
pd.set_option('display.max_colwidth', 15)
pd.set_option('display.width', 1000)

print(df)

# --- 重點驗證 ---
print("\n--- 修正驗證 ---")
print(f"輸入 #一6 (應為第5節): {parsed_data[5][1]}") # index 5 is label "5"
print(f"輸入 #四10 (應為第9節): {parsed_data[9][4]}") # index 9 is label "9"
print(f"輸入 #一11 (應為第A節): {parsed_data[10][1]}") # index 10 is label "A"