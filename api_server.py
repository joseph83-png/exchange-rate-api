# -*- coding: utf-8 -*-
"""
後端 API 伺服器 (最終版)
- 提供 /get_all_rates 端點，查詢指定日期的所有匯率。
- 保留了 /get_rate 端點，以備不時之需。
"""
import sys
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify
from flask_cors import CORS

def fetch_all_bot_rates(target_date: str):
    all_rates_data = []
    try:
        url = f"https://rate.bot.com.tw/xrt/all/{target_date}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        rate_table = soup.find('table', class_='table-hover')
        if not rate_table: return []
        currency_rows = rate_table.find('tbody').find_all('tr')
        for row in currency_rows:
            all_tds = row.find_all('td')
            all_rates_data.append({
                "幣別": all_tds[0].find('div', class_='visible-phone').text.strip(),
                "現金匯率_本行買入": all_tds[1].text.strip(),
                "現金匯率_本行賣出": all_tds[2].text.strip(),
                "即期匯率_本行買入": all_tds[3].text.strip(),
                "即期匯率_本行賣出": all_tds[4].text.strip()
            })
        return all_rates_data
    except Exception as e:
        print(f"Error in fetch_all_bot_rates: {e}", file=sys.stderr)
        return []

def fetch_bot_exchange_rate(target_date: str, currency_code: str):
    if currency_code == "TWD": return "1"
    try:
        all_rates = fetch_all_bot_rates(target_date)
        if not all_rates: return None
        found = next((rate for rate in all_rates if currency_code in rate.get("幣別", "")), None)
        if found:
            rate_value = found.get("即期匯率_本行賣出")
            return rate_value if rate_value and rate_value != '-' else None
        return None
    except Exception as e:
        print(f"Error in fetch_bot_exchange_rate: {e}", file=sys.stderr)
        return None

app = Flask(__name__)
CORS(app)

@app.route('/get_all_rates', methods=['GET'])
def get_all_rates_api():
    query_date = request.args.get('date')
    if not query_date: return jsonify({'error': '缺少 date 參數'}), 400
    all_rates = fetch_all_bot_rates(query_date)
    if all_rates: return jsonify(all_rates)
    else: return jsonify({'error': f'在 {query_date} 找不到任何匯率資料'}), 404

@app.route('/get_rate', methods=['GET'])
def get_rate_api():
    query_date = request.args.get('date')
    query_currency = request.args.get('currency')
    if not query_date or not query_currency:
        return jsonify({'error': '缺少 date 或 currency 參數'}), 400
    rate = fetch_bot_exchange_rate(query_date, query_currency)
    if rate: return jsonify({'rate': rate})
    else: return jsonify({'error': f'在 {query_date} 找不到 {query_currency} 的匯率，或當日非營業日'}), 404

if __name__ == '__main__':
    app.run(port=5000, debug=True)