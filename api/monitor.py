import time
import hmac
import base64
import hashlib
import requests
from datetime import datetime
import os
from http.server import BaseHTTPRequestHandler
import json

API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TARGET_COIN = "USDC"
BASE_URL = "https://api.bitget.com"
PRICE_LOW = 0.9995
PRICE_HIGH = 0.9997

def generate_signature(timestamp, method, request_path, body=""):
    message = timestamp + method + request_path + body
    mac = hmac.new(SECRET_KEY.encode("utf-8"), message.encode("utf-8"), hashlib.sha256)
    return base64.b64encode(mac.digest()).decode()

def get_headers(method, request_path, body=""):
    timestamp = str(int(time.time() * 1000))
    sign = generate_signature(timestamp, method, request_path, body)
    return {
        "ACCESS-KEY": API_KEY,
        "ACCESS-SIGN": sign,
        "ACCESS-TIMESTAMP": timestamp,
        "ACCESS-PASSPHRASE": PASSPHRASE,
        "Content-Type": "application/json",
        "locale": "zh-CN"
    }

def send_bark_notification(message):
    try:
        bark_url = f"https://api.day.app/oEDx8a23HFJGCS7GNzmHrL/{message}"
        response = requests.get(bark_url, timeout=10)
        return response.status_code == 200
    except:
        return False

def check_earn_status(coin):
    try:
        request_path = f"/api/v2/earn/savings/product?coin={coin}"
        headers = get_headers("GET", request_path)
        response = requests.get(BASE_URL + request_path, headers=headers, timeout=10)
        
        # 返回详细的错误信息
        if response.status_code != 200:
            try:
                error_data = response.json()
                return False, f"API错误 {response.status_code}: {error_data}"
            except:
                return False, f"API错误 {response.status_code}: {response.text}"
        
        data = response.json()
        if data.get("code") == "00000":
            for product in data.get("data", []):
                if product.get("coin") == coin and (product.get("status") == "in_progress" or product.get("canPurchase")):
                    return True, f"{coin} 简单赚币可申购"
            return False, f"{coin} 简单赚币暂不可申购"
        else:
            return False, f"API返回错误: {data}"
    except Exception as e:
        return False, f"检查失败: {str(e)}"

def get_usdc_usdt_price():
    try:
        url = "https://api.bitget.com/api/spot/v1/market/ticker?symbol=usdcusdt_spbl"
        data = requests.get(url, timeout=10).json()
        return float(data['data']['close']), None
    except Exception as e:
        return None, f"获取价格失败: {e}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            results = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "earn_status": {},
                "price_status": {},
                "notifications": [],
                "debug": {
                    "has_api_key": bool(API_KEY),
                    "has_secret": bool(SECRET_KEY),
                    "has_passphrase": bool(PASSPHRASE)
                }
            }
            is_available, message = check_earn_status(TARGET_COIN)
            results["earn_status"] = {"coin": TARGET_COIN, "available": is_available, "message": message}
            if is_available and send_bark_notification(f"{TARGET_COIN}简单赚币已开放"):
                results["notifications"].append(f"✅ {TARGET_COIN} 开放通知已发送")
            price, error = get_usdc_usdt_price()
            if price:
                results["price_status"] = {
                    "price": price,
                    "low_threshold": PRICE_LOW,
                    "high_threshold": PRICE_HIGH,
                    "alert": price <= PRICE_LOW or price >= PRICE_HIGH
                }
                if (price <= PRICE_LOW or price >= PRICE_HIGH) and send_bark_notification(f"⚠️USDC/USDT价格异常:{price}"):
                    results["notifications"].append(f"✅ 价格异常通知已发送: {price}")
            else:
                results["price_status"] = {"error": error}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results, ensure_ascii=False, indent=2).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    def do_POST(self):
        self.do_GET()
