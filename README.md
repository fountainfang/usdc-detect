# Arbitrage Monitor Bot (Binance & Bitget)

This is an automated arbitrage monitoring system developed in Python, designed to monitor real-time price discrepancies (Bid Price Gap) for the **USDC/USDT** pair between **Binance** and **Bitget** exchanges. The system integrates a Telegram Bot control interface and Bark push notifications to provide immediate data support for high-frequency decision-making.



## 🌟 Core Features

* **Real-time Data Ingestion**: Utilizes asynchronous polling to fetch the latest Order Book (bookTicker) data from Binance and Bitget REST APIs every 5 seconds.
* **Intelligent Strategy Logic**:
    * **Spread Calculation**: Automatically compares Bid prices across exchanges and calculates the absolute spread.
    * **Strategy Recommendation**: Suggests "Maker Buy" vs. "Taker Sell" combinations based on the direction of the price gap.
* **Multi-level Alerting Mechanism**:
    * Dynamically adjusts notification frequency based on spread size: Alerts every 1 minute for spreads $\ge 0.0002$; every 2 minutes for spreads $\ge 0.0001$.
    * Supports dual-channel notifications via **Bark** (iOS push) and **Telegram**.
* **Interactive Telegram Console**:
    * Features a custom menu (`ReplyKeyboardMarkup`) for commands like `/start`, `/stop`, `/pause`, and `/status`.
    * **Smart Pause (`/pause`)**: Mutes notifications when prices are stagnant and automatically resumes when a price change is detected.
* **Robust Design**: Includes comprehensive exception handling, logging, and secure configuration management using `.env`.

## 🛠️ Tech Stack

* **Language**: Python 3.x
* **Core Libraries**: `python-telegram-bot` (Asynchronous bot framework), `requests` (API communication), `python-dotenv` (Environment management).
* **API Integrations**: Binance Spot API, Bitget Spot API v2.
* **Push Services**: Bark API, Telegram Bot API.

## 🚀 Quick Start

### 1. Prerequisites
Install the required Python dependencies:
```bash
pip install python-telegram-bot requests python-dotenv


### 2. Configuration
Create a `.env` file in the root directory and fill in your credentials:

```env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
BARK_URL="your_bark_server_url"


### 3. Run the Bot
Bash
python main.py
