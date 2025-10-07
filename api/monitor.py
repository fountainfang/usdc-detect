import time
import hmac
import base64
import hashlib
import requests
from datetime import datetime
import os
from http.server import BaseHTTPRequestHandler
import json

# ========== 配置 ==========
API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

# Bark 通知 URL
BARK_URL = "https://api.day.app/oEDx8a23HFJGCS7GNzmHrL/简单赚币已开放"

# 检测币种
TARGET_COIN = "USDC"

# Bitget API 基础地址
BASE_URL = "https://api.bitget.com"

# USDC/USDT 价格监控
PRICE_LOW = 0.9991
PRICE_HIGH = 0.9997


# ========== 工具函数 ==========
def generate_signature(timestamp, method, request_path, body=""):
    """生成 Bitget API 签名"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    )
    return base64.b64encode(mac.digest()).decode()


def get_headers(method, request_path, body=""):
    """生成请求头"""
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
    """发送 Bark 通知"""
    try:
        bark_url = f"https://api.day.app/oEDx8a23HFJGCS7GNzmHrL/{message}"
        response = requests.get(bark_url, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 通知发送异常: {e}")
        return False


def check_earn_status(coin):
    """检查指定币种的简单赚币是否可申购"""
    try:
        request_path = f"/api/v2/earn/savings/product?coin={coin}"
        method = "GET"

        headers = get_headers(method, request_path)
        url = BASE_URL + request_path

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "00000":
                products = data.get("data", [])

                for product in products:
                    coin_name = product.get("coin")
                    status = product.get("status", "")
                    can_purchase = product.get("canPurchase", False)

                    if coin_name == coin and (status == "in_progress" or can_purchase):
                        return True, f"{coin} 简单赚币可申购"

                return False, f"{coin} 简单赚币暂不可申购"
            else:
                return False, f"API 错误: {data.get('msg')}"
        else:
            return False, f"请求失败: {response.status_code}"

    except Exception as e:
        return False, f"检查失败: {e}"


def get_usdc_usdt_price():
    """获取 USDC/USDT 最新价格"""
    try:
        url = "https://api.bitget.com/api/spot/v1/market/ticker?symbol=usdcusdt_spbl"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        price = float(data['data']['close'])
        return price, None
    except Exception as e:
        return None, f"获取价格失败: {e}"


class handler(BaseHTTPRequestHandler):
    """Vercel Serverless Function Handler"""
    
    def do_GET(self):
        try:
            results = {
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "earn_status": {},
                "price_status": {},
                "notifications": []
            }

            # 1. 检查简单赚币状态
            is_available, message = check_earn_status(TARGET_COIN)
            results["earn_status"] = {
                "coin": TARGET_COIN,
                "available": is_available,
                "message": message
            }

            if is_available:
                if send_bark_notification(f"{TARGET_COIN}简单赚币已开放"):
                    results["notifications"].append(f"✅ {TARGET_COIN} 开放通知已发送")

            # 2. 检查价格
            price, error = get_usdc_usdt_price()
            if price is not None:
                results["price_status"] = {
                    "price": price,
                    "low_threshold": PRICE_LOW,
                    "high_threshold": PRICE_HIGH,
                    "alert": price <= PRICE_LOW or price >= PRICE_HIGH
                }

                if price <= PRICE_LOW or price >= PRICE_HIGH:
                    if send_bark_notification(f"⚠️USDC/USDT价格异常:{price}"):
                        results["notifications"].append(f"✅ 价格异常通知已发送: {price}")
            else:
                results["price_status"] = {"error": error}

            # 返回结果
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(results, ensure_ascii=False, indent=2).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode())

    def do_POST(self):
        """支持 POST 请求（用于 cron job）"""
        self.do_GET()