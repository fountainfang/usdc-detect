import os
import time
import requests
import json
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Load environment variables
load_dotenv()

BARK_URL = os.getenv("BARK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_binance_price():
    """Refer to https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#symbol-order-book-ticker"""
    try:
        url = "https://api.binance.com/api/v3/ticker/bookTicker?symbol=USDCUSDT"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
             "bid": float(data['bidPrice']),
             "ask": float(data['askPrice'])
        }
    except Exception as e:
        print(f"Error fetching Binance price: {e}")
        return None

def get_bitget_price():
    """Refer to https://www.bitget.com/api-doc/spot/market/Get-Tickers"""
    try:
        url = "https://api.bitget.com/api/v2/spot/market/tickers?symbol=USDCUSDT"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data['code'] != '00000':
             print(f"Bitget API Error: {data}")
             return None
        
        # Bitget data is a list
        ticker = data['data'][0]
        return {
            "bid": float(ticker['bidPr']),
            "ask": float(ticker['askPr'])
        }
    except Exception as e:
        print(f"Error fetching Bitget price: {e}")
        return None

def send_bark_notification(title, content):
    if not BARK_URL:
        return

    try:
        # Clean up BARK_URL if it has quotes or whitespace
        clean_bark_url = BARK_URL.strip().strip('"').strip("'")
        base_url = clean_bark_url.rstrip('/')
        url = f"{base_url}/{title}/{content}"
        requests.get(url, timeout=5)
        print(f"Bark Notification sent: {title}")
    except Exception as e:
        print(f"Error sending Bark notification: {e}")

async def check_arbitrage(context: ContextTypes.DEFAULT_TYPE):
    """Job to check arbitrage opportunities."""
    
    # Store state in bot_data or use a global if needed, but bot_data is cleaner
    # We need last_alert_time per job? Or global?
    # Since checking is global, let's store in bot_data
    if 'last_alert_time' not in context.bot_data:
        context.bot_data['last_alert_time'] = 0

    binance = get_binance_price()
    bitget = get_bitget_price()

    if binance and bitget:
        # Check Pause Logic
        if context.bot_data.get('pause_active'):
             paused_prices = context.bot_data.get('paused_prices')
             current_prices = (binance['bid'], bitget['bid'])
             
             if paused_prices == current_prices:
                 print("Paused and prices unchanged. Skipping.")
                 return
             else:
                 # Prices changed, resume!
                 context.bot_data['pause_active'] = False
                 context.bot_data['paused_prices'] = None
                 print("Prices changed! Resuming notifications.")

        # Strategy: Compare Bid vs Bid (Price Gap)
        # Use absolute difference as requested
        spread = abs(binance['bid'] - bitget['bid'])
        
        direction = ""
        buy_exchange = ""
        sell_exchange = ""
        buy_price = 0.0
        sell_price = 0.0

        if binance['bid'] > bitget['bid']:
            direction = "Binance Bid > Bitget Bid"
            buy_exchange = "Bitget"
            sell_exchange = "Binance"
            buy_price = bitget['bid']
            sell_price = binance['bid']
        else:
            direction = "Bitget Bid > Binance Bid"
            buy_exchange = "Binance"
            sell_exchange = "Bitget"
            buy_price = binance['bid']
            sell_price = bitget['bid']

        # Format spread
        # Detailed Log
        # Use round to assume 0.0001 is significant even if float is 0.00009999
        if round(spread, 5) >= 0.0001:
             header = "✅ Potential Opportunity"
        else:
             header = "zzZ Low Spread"

        log_msg = (
            f"--- {header} ---\n"
            f"Bid Gap: {spread:.5f} ({direction})\n"
            f"  Binance Bid: {binance['bid']:.4f}\n"
            f"  Bitget  Bid: {bitget['bid']:.4f}\n"
            f"  Strategy: Buy {buy_exchange} (Maker @ {buy_price}) -> Sell {sell_exchange} (Taker @ {sell_price})"
        )
        print(log_msg)
        
        # Save last check info for /status command
        context.bot_data['last_check_info'] = log_msg
        context.bot_data['last_check_time'] = time.time()

        current_time = time.time()
        last_alert_time = context.bot_data['last_alert_time']
        interval = 0

        # Use rounded spread for consistent alerting with logs
        check_spread = round(spread, 5)

        if check_spread >= 0.0002:
            interval = 60 # 1 minute
        elif check_spread >= 0.0001:
            interval = 120 # 2 minutes
        else:
            interval = 0 # No alert

        if interval > 0:
            if current_time - last_alert_time >= interval:
                title = "Arbitrage_Alert"
                content = f"Spread:{spread:.5f}_{direction}_Buy:{buy_exchange}_Sell:{sell_exchange}"
                
                # Send Bark
                send_bark_notification(title, content)
                
                # Send Telegram (if configured, optional but good for feedback)
                # Ensure we have a chat_id to send to. 
                # If started via /start, we likely have context.job.chat_id if we passed it?
                # The job 'check_arbitrage' doesn't automatically know the chat_id unless passed in context or stored.
                # Let's simple rely on Bark as requested, or send to TELEGRAM_CHAT_ID if set.
                if TELEGRAM_CHAT_ID:
                     chat_id = TELEGRAM_CHAT_ID.strip().strip('"').strip("'")
                     try:
                         await context.bot.send_message(chat_id=chat_id, text=f"🔔 {title}\n{content.replace('_', ' ')}\n{log_msg}")
                     except Exception as e:
                         print(f"Error sending Telegram alert: {e}")

                context.bot_data['last_alert_time'] = current_time

    # Update latest prices for pause command
    context.bot_data['latest_prices'] = (binance['bid'], bitget['bid'])

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# ... imports ...

# Define keyboard layout
KEYBOARD = [['/start', '/stop'], ['/pause', '/status']]
REPLY_MARKUP = ReplyKeyboardMarkup(KEYBOARD, resize_keyboard=True)

# ... (rest of imports and setup) ...

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the arbitrage monitoring."""
    chat_id = update.effective_chat.id
    
    # Check authorization
    if TELEGRAM_CHAT_ID:
        config_chat_id = TELEGRAM_CHAT_ID.strip().strip('"').strip("'")
        if str(chat_id) != str(config_chat_id):
            await context.bot.send_message(chat_id=chat_id, text="⛔ Not authorized.")
            return

    # Check if already running
    current_jobs = context.job_queue.get_jobs_by_name("arbitrage_job")
    if current_jobs:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ Monitor is already running.",
            reply_markup=REPLY_MARKUP
        )
        return

    # Add job to queue, run every 5 seconds
    context.job_queue.run_repeating(check_arbitrage, interval=5, first=1, name="arbitrage_job", chat_id=chat_id)
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text="✅ Arbitrage monitor started.\nChecking every 5 seconds.",
        reply_markup=REPLY_MARKUP
    )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stops the arbitrage monitoring."""
    chat_id = update.effective_chat.id
    
    # Check authorization
    if TELEGRAM_CHAT_ID:
        config_chat_id = TELEGRAM_CHAT_ID.strip().strip('"').strip("'")
        if str(chat_id) != str(config_chat_id):
           await context.bot.send_message(chat_id=chat_id, text="⛔ Not authorized.")
           return

    current_jobs = context.job_queue.get_jobs_by_name("arbitrage_job")
    if not current_jobs:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ Monitor is not running.",
            reply_markup=REPLY_MARKUP
        )
        return

    for job in current_jobs:
        job.schedule_removal()
    
    # Reset pause state on stop
    context.bot_data['pause_active'] = False
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text="zzZ Arbitrage monitor stopped.",
        reply_markup=REPLY_MARKUP
    )

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pauses notifications until prices change."""
    chat_id = update.effective_chat.id

    # Check authorization
    if TELEGRAM_CHAT_ID:
        config_chat_id = TELEGRAM_CHAT_ID.strip().strip('"').strip("'")
        if str(chat_id) != str(config_chat_id):
            return

    if 'latest_prices' not in context.bot_data:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ No price data yet. Wait for a check cycle.", reply_markup=REPLY_MARKUP)
        return
    
    context.bot_data['paused_prices'] = context.bot_data['latest_prices']
    context.bot_data['pause_active'] = True
    
    prices = context.bot_data['latest_prices']
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⏸️ Paused.\nNotifications muted until Bid prices change from:\nBinance: {prices[0]}\nBitget: {prices[1]}",
        reply_markup=REPLY_MARKUP
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks the status and last result."""
    chat_id = update.effective_chat.id
    
    # Check authorization
    if TELEGRAM_CHAT_ID:
        config_chat_id = TELEGRAM_CHAT_ID.strip().strip('"').strip("'")
        if str(chat_id) != str(config_chat_id):
            return 

    current_jobs = context.job_queue.get_jobs_by_name("arbitrage_job")
    is_running = len(current_jobs) > 0
    
    status_emoji = "✅ Running" if is_running else "zzZ Stopped"
    
    msg = f"Status: {status_emoji}\n"
    
    if context.bot_data.get('pause_active'):
        msg += "⏸️ PAUSED (Waiting for price change)\n"
    
    if 'last_check_info' in context.bot_data:
        msg += f"\nLast Check:\n{context.bot_data['last_check_info']}"
    else:
        msg += "\nNo check data available yet."

    await context.bot.send_message(
        chat_id=chat_id, 
        text=msg,
        reply_markup=REPLY_MARKUP
    )

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN is not set in .env")
        exit(1)
        
    # Clean token
    token = TELEGRAM_BOT_TOKEN.strip().strip('"').strip("'")
    
    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    stop_handler = CommandHandler('stop', stop)
    pause_handler = CommandHandler('pause', pause)
    status_handler = CommandHandler('status', status)
    
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(pause_handler)
    application.add_handler(status_handler)
    
    print("Telegram Bot is polling...")
    application.run_polling()
