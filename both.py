"""
KAS Grid Bot - Version Simple
"""

import os
import time
import logging
from pybit.unified_trading import HTTP
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Get API Keys from environment
API_KEY = os.getenv("AVKLVzE3M9dEaQ8WoY")
API_SECRET = os.getenv("d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel")

if not API_KEY or not API_SECRET:
    log.error("❌ API_KEY or API_SECRET missing!")
    exit(1)

# Connect to Bybit
try:
    session = HTTP(
        testnet=False,
        api_key=API_KEY,
        api_secret=API_SECRET,
    )
    log.info("✅ Connected to Bybit")
except Exception as e:
    log.error(f"❌ Connection failed: {e}")
    exit(1)

# Grid settings
SYMBOL = "KASUSDT"
GRID_LOWER = 0.034
GRID_UPPER = 0.060
GRID_STEP = 0.002
CAPITAL = 100.0

# Build grid levels
GRID_LEVELS = []
price = GRID_LOWER
while price <= GRID_UPPER + 0.0001:
    GRID_LEVELS.append(round(price, 3))
    price += GRID_STEP

ORDER_SIZE = CAPITAL / len(GRID_LEVELS)

log.info(f"🚀 Grid Bot Starting")
log.info(f"   Levels: {len(GRID_LEVELS)}")
log.info(f"   Order Size: ${ORDER_SIZE:.2f}")
log.info(f"   Levels: {GRID_LEVELS}")

# Track orders
active_buys = {}
active_sells = {}
total_profit = 0.0

def get_price():
    try:
        resp = session.get_tickers(category="spot", symbol=SYMBOL)
        return float(resp["result"]["list"][0]["lastPrice"])
    except:
        return None

def get_balance():
    try:
        resp = session.get_wallet_balance(accountType="UNIFIED", coin="USDT")
        usdt = float(resp["result"]["list"][0]["coin"][0]["availableToWithdraw"])
        resp = session.get_wallet_balance(accountType="UNIFIED", coin="KAS")
        kas = float(resp["result"]["list"][0]["coin"][0]["availableToWithdraw"])
        return usdt, kas
    except:
        return 0.0, 0.0

def place_buy(price):
    try:
        qty = round(ORDER_SIZE / price, 2)
        if qty <= 0:
            return None
        session.place_order(
            category="spot",
            symbol=SYMBOL,
            side="Buy",
            orderType="Limit",
            qty=str(qty),
            price=str(price),
            timeInForce="GTC",
        )
        log.info(f"🟢 BUY  | {qty} KAS @ ${price:.3f}")
        return True
    except Exception as e:
        log.error(f"❌ Buy failed: {e}")
        return None

def place_sell(price, qty):
    try:
        qty = round(qty * 0.99, 2)
        if qty <= 0:
            return None
        session.place_order(
            category="spot",
            symbol=SYMBOL,
            side="Sell",
            orderType="Limit",
            qty=str(qty),
            price=str(price),
            timeInForce="GTC",
        )
        log.info(f"🔴 SELL | {qty} KAS @ ${price:.3f}")
        return True
    except Exception as e:
        log.error(f"❌ Sell failed: {e}")
        return None

# Main loop
cycle = 0
while True:
    try:
        cycle += 1
        price = get_price()
        usdt, kas = get_balance()

        if price is None:
            log.warning("⚠️  Failed to get price")
            time.sleep(60)
            continue

        log.info(f"Cycle #{cycle} | Price: ${price:.4f} | USDT: ${usdt:.2f} | KAS: {kas:.2f}")

        # First cycle: place buy orders below current price
        if cycle == 1:
            buy_levels = [l for l in GRID_LEVELS if l < price]
            for level in buy_levels:
                place_buy(level)
                time.sleep(0.5)
            log.info(f"✅ Placed {len(buy_levels)} buy orders")

        # Sleep 4 hours
        log.info(f"😴 Sleeping 4 hours...")
        time.sleep(4 * 3600)

    except KeyboardInterrupt:
        log.info("⏹️  Stopped")
        break
    except Exception as e:
        log.error(f"❌ Error: {e}")
        time.sleep(300)
