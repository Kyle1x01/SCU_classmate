# config.py
import json
import os
import base64

CONFIG_FILE = "config.json"

def load_config():
    """讀取設定檔"""
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 嘗試解碼密碼
            if "password" in data and data["password"]:
                try:
                    data["password"] = base64.b64decode(data["password"]).decode("utf-8")
                except:
                    data["password"] = "" # 解碼失敗就清空
            return data
    except Exception as e:
        print(f"Config load error: {e}")
        return {}

def save_config(username, password, remember_me):
    """儲存設定檔"""
    data = {
        "remember_me": remember_me,
        "username": username if remember_me else "",
        # 如果勾選記住，則將密碼編碼後儲存；否則存空字串
        "password": base64.b64encode(password.encode("utf-8")).decode("utf-8") if remember_me else ""
    }
    
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Config save error: {e}")