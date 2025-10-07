# monitor.py
import time
import hmac
import base64
import hashlib
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

API_KEY = os.getenv("BITGET_API_KEY")
SECRET_KEY = os.getenv("BITGET_SECRET_KEY")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")

TARGET_COIN = "USDC"      # 可改成 "USDT"
PRICE_LOW = 0.9991        # USDC/USDT 下限
PRICE_HIGH = 0.9997       # USDC/USDT 上限
BASE_URL = "https://api.bitget.com"

# Bark 通知
BARK_URL_PREFIX = "https://api.day.app/oEDx8a23HFJGCS7GNzmHrL/"

# ---------------- 工具函数 ----------------
def generate_signature(timestamp, method, request_path, body=""):
    message = timestamp + method + request_path + body
    mac = hmac.new(
        SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    )
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
    """发送 Bark 通知"""
    try:
        bark_url = BARK_URL_PREFIX + message
        response = requests.get(bark_url, timeout=10)
        if response.status_code == 200:
            print(f"📱 通知发送成功: {message}")
            return True
        else:
            print(f"⚠️ 通知发送失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 通知异常: {e}")
        return False

def check_earn_status(coin):
    """检查简单赚币申购状态"""
    try:
        request_path = f"/api/v2/earn/savings/product?coin={coin}"
        method = "GET"
        headers = get_headers(method, request_path)
        url = BASE_URL + request_path

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            return False

        data = response.json()
        if data.get("code") != "00000":
            print(f"⚠️ API 返回错误码: {data.get('code')} - {data.get('msg')}")
            return False

        products = data.get("data", [])
        for product in products:
            coin_name = product.get("coin")
            status = product.get("status", "")
            can_purchase = product.get("canPurchase", False)
            if coin_name == coin and (status == "in_progress" or can_purchase):
                print(f"✅ {coin} 简单赚币可申购")
                send_bark_notification(f"{coin} 简单赚币已开放")
                return True

        print(f"❌ {coin} 简单赚币暂不可申购")
        return False

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

def get_usdc_usdt_price():
    """获取 USDC/USDT 最新价格"""
    try:
        url = "https://api.bitget.com/api/spot/v1/market/ticker?symbol=usdcusdt_spbl"
        resp = requests.get(url, timeout=10)
        data = resp.json()
        price = float(data['data']['close'])
        print(f"💰 USDC/USDT 当前价格: {price}")
        return price
    except Exception as e:
        print(f"❌ 获取价格失败: {e}")
        return None

# ---------------- 主函数 ----------------
def run_monitor():
    """单次执行监控"""
    print(f"🔍 开始监控 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")

    # 检查简单赚币
    check_earn_status(TARGET_COIN)

    # 检查 USDC/USDT 价格
    price = get_usdc_usdt_price()
    if price is not None and (price <= PRICE_LOW or price >= PRICE_HIGH):
        send_bark_notification(f"⚠️ USDC/USDT 价格异常: {price}")

    return {"status": "ok"}
