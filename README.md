# 🤖 Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application that places orders on the
[Binance Futures Testnet](https://testnet.binancefuture.com) (USDT-M perpetuals).

---

## 📁 Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py          # Package init
│   ├── client.py            # Binance REST API wrapper (auth, signing, requests)
│   ├── orders.py            # Order placement logic + pretty output
│   ├── validators.py        # Input validation layer
│   └── logging_config.py    # Centralized logging setup
├── logs/
│   ├── market_order_sample.log
│   └── limit_order_sample.log
├── cli.py                   # CLI entry point (argparse)
├── .env.example             # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup

### 1. Get Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub or Google account
3. Navigate to **API Management** → generate a new key pair
4. Copy your **API Key** and **API Secret**

### 2. Clone & Install

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/trading_bot.git
cd trading_bot

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials

```bash
# Copy the example env file
cp .env.example .env

# Open .env and fill in your credentials
nano .env   # or use any text editor
```

Your `.env` file should look like:

```
BINANCE_API_KEY=your_actual_api_key
BINANCE_API_SECRET=your_actual_api_secret
```

> ⚠️ **Never commit your `.env` file.** It is already listed in `.gitignore`.

---

## 🚀 How to Run

All commands are run from the project root:

```bash
python cli.py <command> [options]
```

### Place a Market Order

```bash
# Market BUY 0.001 BTC
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# Market SELL 0.01 ETH
python cli.py order --symbol ETHUSDT --side SELL --type MARKET --quantity 0.01
```

### Place a Limit Order

```bash
# Limit BUY — buy BTC if it drops to $50,000
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 50000

# Limit SELL — sell BTC at $65,000
python cli.py order --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 65000

# Limit with IOC time-in-force
python cli.py order --symbol BTCUSDT --side BUY --type LIMIT --quantity 0.001 --price 55000 --tif IOC
```

### Stop-Market Order (Bonus)

```bash
# Stop-Market: trigger a SELL if price drops to $50,000
python cli.py order --symbol BTCUSDT --side SELL --type STOP_MARKET --quantity 0.001 --price 50000
```

### View Account Balances

```bash
python cli.py account
```

### List Open Orders

```bash
# All open orders
python cli.py open-orders

# Filter by symbol
python cli.py open-orders --symbol BTCUSDT
```

### Cancel an Order

```bash
python cli.py cancel --symbol BTCUSDT --order-id 3951899201
```

---

## 🖥️ Sample Output

### Market BUY

```
╔══════════════════════════════════════════════════════╗
║         🤖  Binance Futures Testnet Trading Bot       ║
╚══════════════════════════════════════════════════════╝

────────────────────────────────────────────────────────────
📋  ORDER REQUEST SUMMARY
────────────────────────────────────────────────────────────
  Symbol     : BTCUSDT
  Side       : BUY
  Type       : MARKET
  Quantity   : 0.001
────────────────────────────────────────────────────────────
✅  ORDER RESPONSE
────────────────────────────────────────────────────────────
  Order ID      : 3951822764
  Client OID    : x-Cb7ytekJb3e9b0f3c2f1e1
  Symbol        : BTCUSDT
  Side          : BUY
  Type          : MARKET
  Status        : FILLED
  Orig Qty      : 0.001
  Executed Qty  : 0.001
  Avg Price     : 57823.50
  Time in Force : GTC
  Update Time   : 1720617722104
────────────────────────────────────────────────────────────
🎉  Order placed successfully! Order ID: 3951822764
```

---

## 📄 Logging

Logs are automatically written to `logs/trading_bot_YYYYMMDD.log`.

- **File handler**: captures `DEBUG` and above — every API request, response, and error
- **Console handler**: shows `INFO` and above — clean, human-readable output only

Log format:
```
2025-07-10 14:22:01 | INFO     | client | Placing order → symbol=BTCUSDT side=BUY type=MARKET qty=0.001
```

Sample log files for a market and limit order are included in the `logs/` directory.

---

## 🏗️ Architecture

| Layer | File | Responsibility |
|---|---|---|
| CLI | `cli.py` | Argument parsing, sub-command routing |
| Orders | `bot/orders.py` | Orchestrates validation → API call → output |
| Client | `bot/client.py` | HMAC signing, HTTP requests, error parsing |
| Validators | `bot/validators.py` | Input validation, raises `ValidationError` |
| Logging | `bot/logging_config.py` | Shared logger (file + console) |

The CLI layer never talks to the API directly — it delegates to `orders.py`, which in turn uses `client.py`. This separation makes each layer independently testable.

---

## 🎁 Bonus Features

| Feature | Status |
|---|---|
| `STOP_MARKET` order type | ✅ Implemented |
| `open-orders` sub-command | ✅ Implemented |
| `cancel` sub-command | ✅ Implemented |
| `account` balance viewer | ✅ Implemented |
| Time-in-force (`--tif`) flag | ✅ Implemented |

---

## ⚠️ Assumptions

1. All orders are placed on the **Futures Testnet** only — base URL is hardcoded to `https://testnet.binancefuture.com`.
2. Credentials are loaded from a `.env` file using `python-dotenv`. Alternatively, they can be exported as environment variables before running.
3. STOP_MARKET orders use the `--price` flag as the `stopPrice` parameter.
4. Quantity precision must match the symbol's rules on the testnet — e.g., BTCUSDT requires minimum 0.001 BTC.
5. The bot does **not** manage position sizing, leverage, or margin — this is a minimal order-placement tool.

---

## 🐍 Requirements

- Python 3.8+
- `requests` — HTTP client
- `python-dotenv` — loads `.env` credentials

See `requirements.txt` for pinned versions.
