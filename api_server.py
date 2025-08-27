# -*- coding: utf-8 -*-
"""
後端 API 伺服器
使用 Flask 建立，提供一個 /get_rate 的 API 端點。
接收 date 和 currency 參數，爬取台灣銀行網站，回傳即期賣出匯率。
"""
import sys
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- 核心爬蟲邏輯 ---
def fetch_bot_exchange_rate(target_date: str, currency_code: str):
    """
    從台灣銀行網站爬取指定日期與幣別的即期賣出匯率。
    """
    if currency_code == "TWD":
        return "1"

    try:
        url = f"https://rate.bot.com.tw/xrt/all/{target_date}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 定位包含目標貨幣 (例如 'EUR') 的 div 元素
        currency_div = soup.find('div', class_='visible-phone print_hide', string=currency_code)
        if not currency_div:
            print(f"在 {target_date} 找不到貨幣 {currency_code} 的 div。", file=sys.stderr)
            return None

        # 從 div 往上層找到整個表格列 <tr>
        target_row = currency_div.find_parent('tr')
        if not target_row:
            print(f"找不到 {currency_code} 對應的 <tr>。", file=sys.stderr)
            return None

        # 在該列中找到所有的儲存格 <td>
        all_tds = target_row.find_all('td')
        
        # 「即期匯率-本行賣出」是第 5 個儲存格，其索引為 4
        if len(all_tds) > 4:
            rate = all_tds[4].text.strip()
            # 如果儲存格內容不是 '-'，則回傳該值
            return rate if rate and rate != '-' else None
        else:
            print(f"{currency_code} 的 <tr> 中儲存格數量不足。", file=sys.stderr)
            return None

    except requests.exceptions.RequestException as e:
        print(f"網路請求失敗: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"處理爬蟲時發生未預期的錯誤: {e}", file=sys.stderr)
        return None

# --- 建立 Flask 伺服器 ---
app = Flask(__name__)
# 啟用 CORS，允許來自任何來源的網頁請求，解決跨域問題
CORS(app)

# --- 定義 API 端點 (Endpoint) ---
@app.route('/get_rate', methods=['GET'])
def get_rate_api():
    """
    API 的主要處理函式
    """
    # 從請求的 URL 中獲取參數 (e.g., /get_rate?date=2025-08-27&currency=EUR)
    query_date = request.args.get('date')
    query_currency = request.args.get('currency')

    # 驗證參數是否存在
    if not query_date or not query_currency:
        return jsonify({'error': '缺少 date 或 currency 參數'}), 400

    print(f"收到查詢請求: 日期={query_date}, 幣別={query_currency}")

    # 執行爬蟲函式
    rate = fetch_bot_exchange_rate(query_date, query_currency)

    # 根據結果回傳 JSON
    if rate:
        print(f"查詢成功: 匯率={rate}")
        return jsonify({'rate': rate})
    else:
        print("查詢失敗: 找不到對應匯率或發生錯誤")
        return jsonify({'error': f'在 {query_date} 找不到 {query_currency} 的匯率，或當日非營業日'}), 404

# --- 程式主入口 ---
if __name__ == '__main__':
    # 在本機運行伺服器，監聽 port 5000
    # debug=True 會在程式碼變更時自動重啟，方便開發
    app.run(port=5000, debug=True)