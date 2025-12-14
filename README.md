# 🐱 東吳課表魔法貓貓 (SCU Classmate)

> 專為東吳大學 (Soochow University) 學生設計的課表美化神器。
> 告別傳統醜醜的系統截圖，一鍵生成高畫質、排版精美的課表圖片！

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![GUI](https://img.shields.io/badge/UI-CustomTkinter-green.svg)
![Platform](https://img.shields.io/badge/Platform-macOS-lightgrey.svg)

## ✨ 專案簡介 (Introduction)

**SCU_classmate** 是一個基於 Python 開發的桌面應用程式。它解決了學校選課系統課表排版不佳、難以截圖保存的問題。透過自動化爬蟲技術，直接從校務系統抓取你的課程資訊，並重新渲染成設計感十足的圖片，方便設定為手機或電腦桌布。

特別針對 **macOS (Apple Silicon)** 進行優化，支援 Retina 高解析度渲染與原生的操作體驗。

## 🚀 功能亮點 (Features)

* **🤖 自動抓取模式**：
    * 整合 `Playwright` 自動化技術，輸入學號密碼即可自動登入校務系統。
    * 自動點擊查詢並解析 HTML，無需手動複製貼上。
* **📝 手動貼上模式**：
    * 擔心帳號安全？支援純文字貼上模式（複製校務系統的課表文字代碼即可解析）。
* **🎨 高畫質渲染**：
    * 使用網頁渲染技術，生成超高解析度 JPG 圖片。
    * 自動處理「單雙週」課程排版，資訊清晰不擁擠。
* **💾 貼心功能**：
    * **記住我**：支援儲存帳號密碼（Base64 編碼儲存於本地），下次開啟免輸入。
    * **智慧縮放**：預覽視窗自動適應螢幕大小。
    * **系統預覽**：支援一鍵呼叫 macOS 原生「預覽程式」開啟圖片，方便列印或標註。
* **🍎 macOS 優化**：
    * 修復 Tkinter 在 Mac 上的複製/貼上 (Cmd+C/V) 快捷鍵問題。
    * 支援視窗置頂與原生選單列整合。

## 🛠️ 技術架構 (Tech Stack)

* **語言**：Python 3.x
* **GUI 框架**：`CustomTkinter` (現代化的 Tkinter 包裝)
* **爬蟲核心**：`Playwright` (處理動態登入與渲染), `BeautifulSoup4` (解析 HTML)
* **圖片處理**：`Pillow (PIL)`
* **設定管理**：JSON + Base64

## 📦 安裝與執行 (Installation)

### 前置需求
請確保電腦已安裝 [Python 3.10+](https://www.python.org/)。

### 1. 下載專案
```bash
git clone [https://github.com/Kyle1x01/SCU_classmate.git](https://github.com/Kyle1x01/SCU_classmate.git)
cd SCU_classmate
