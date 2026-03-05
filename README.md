我明白你的困扰了。Markdown 格式失效通常是因为代码块的起始符号（```）和结束符号（```）没有成对出现。当你复制不完整时，后面的文字都会被误认为包含在代码框里。为了让 Mawardi Muhammad 教授看到最专业的排版，请务必完整复制下面这个代码框里的所有内容（从第一行的 # 到最后一行的 ```）：Markdown# Arbitrage Monitor Bot (Binance & Bitget)

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
* **Core Libraries**: `python-telegram-bot`, `requests`, `python-dotenv`.
* **API Integrations**: Binance Spot API, Bitget Spot API v2.
* **Push Services**: Bark API, Telegram Bot API.

## 🚀 Quick Start

### 1. Prerequisites
Install the required Python dependencies:
```bash
pip install python-telegram-bot requests python-dotenv
2. ConfigurationCreate a .env file in the root directory and fill in your credentials:代码段TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
BARK_URL="your_bark_server_url"
3. Run the BotBashpython main.py
📊 Monitoring Logic FlowThe system executes the following workflow via the check_arbitrage task:Data Retrieval: Concurrent fetching of bookTicker data from Binance and Bitget.State Verification: Checks if the system is in a /pause state; skips notifications if prices haven't moved to avoid redundancy.Spread Analysis:Calculates$$Spread = |Binance_{Bid} - Bitget_{Bid}|$$If $Spread \ge 0.0001$, marks as a Potential Opportunity.Automated Alerting: Manages asynchronous push tasks via context.job_queue based on defined thresholds.
