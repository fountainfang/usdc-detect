# Arbitrage Monitor Bot (Binance & Bitget)

This is an automated arbitrage monitoring system developed in Python,
designed to monitor real-time price discrepancies (Bid Price Gap) for
the **USDC/USDT** pair between **Binance** and **Bitget** exchanges.

The system integrates a Telegram Bot control interface and Bark push
notifications to provide immediate data support for high-frequency
decision-making.

------------------------------------------------------------------------

## 🌟 Core Features

### Real-time Data Ingestion

-   Utilizes asynchronous polling to fetch the latest **Order Book
    (bookTicker)** data\
-   Pulls data from **Binance** and **Bitget REST APIs** every **5
    seconds**

### Intelligent Strategy Logic

-   **Spread Calculation**\
    Automatically compares Bid prices across exchanges and calculates
    the absolute spread.

-   **Strategy Recommendation**\
    Suggests **"Maker Buy" vs. "Taker Sell"** combinations based on the
    direction of the price gap.

### Multi-level Alerting Mechanism

-   Dynamically adjusts notification frequency based on spread size:
    -   Alert **every 1 minute** when spread ≥ `0.0002`
    -   Alert **every 2 minutes** when spread ≥ `0.0001`
-   Supports **dual-channel notifications**:
    -   Bark (iOS push)
    -   Telegram Bot

### Interactive Telegram Console

-   Custom command menu using `ReplyKeyboardMarkup`
-   Commands supported:

```{=html}
<!-- -->
```
    /start
    /stop
    /pause
    /status

-   **Smart Pause (`/pause`)**
    -   Mutes notifications when prices are stagnant
    -   Automatically resumes when price movement is detected

### Robust Design

-   Comprehensive **exception handling**
-   Logging support
-   Secure configuration via `.env` file

------------------------------------------------------------------------

## 🛠 Tech Stack

**Language** - Python 3.x

**Core Libraries** - `python-telegram-bot` - `requests` -
`python-dotenv`

**API Integrations** - Binance Spot API - Bitget Spot API v2

**Push Services** - Bark API - Telegram Bot API

------------------------------------------------------------------------

# 🚀 Quick Start

## 1️⃣ Install Dependencies

``` bash
pip install python-telegram-bot requests python-dotenv
```

------------------------------------------------------------------------

## 2️⃣ Configuration

Create a `.env` file in the project root:

``` env
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
TELEGRAM_CHAT_ID="your_telegram_chat_id"
BARK_URL="your_bark_server_url"
```

------------------------------------------------------------------------

## 3️⃣ Run the Bot

``` bash
python main.py
```

------------------------------------------------------------------------

# 📊 Monitoring Logic Flow

The system executes the following workflow via the `check_arbitrage`
task.

### 1. Data Retrieval

Fetches `bookTicker` data concurrently from:

-   Binance
-   Bitget

------------------------------------------------------------------------

### 2. State Verification

Checks whether the bot is in `/pause` mode.

If prices **haven't changed**, the system skips notifications to prevent
redundant alerts.

------------------------------------------------------------------------

### 3. Spread Analysis

Spread calculation:

    Spread = |Binance_Bid - Bitget_Bid|

If

    Spread ≥ 0.0001

The system marks it as a **Potential Arbitrage Opportunity**.

------------------------------------------------------------------------

### 4. Automated Alerting

Manages asynchronous push notifications using:

    context.job_queue

Alert frequency is dynamically adjusted based on spread thresholds.
