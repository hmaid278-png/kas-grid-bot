import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({'apiKey': api_key, 'secret': api_secret, 'enableRateLimit': True, 'options': {'defaultType': 'unified'}})
exchange.load_markets()

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def get_sma(symbol, period=20):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=period)
    closes = [candle[4] for candle in ohlcv]
    return sum(closes) / len(closes)

def run_kas_bot():
    symbol = 'KAS/USDT'
    asset_name = 'KAS'
    PROFIT_MARGIN = 0.02   
    last_check_price = 0
    last_check_time = 0
    
    print(f"🚀 KAS ACTIVE | 3H CHECK CYCLE | 8H BUY DECISION")

    while True:
        try:
            balance = exchange.fetch_balance()
            usdt_balance = safe_float(balance['total']['USDT'])
            asset_balance = safe_float(balance['total'][asset_name])
            ticker = exchange.fetch_ticker(symbol)
            current_price = safe_float(ticker.get('last'))
            current_time = time.time()
            
            if asset_balance * current_price < 5.0:
                # المقارنة كل 8 ساعات (28800 ثانية)
                if current_time - last_check_time >= 28800:
                    sma_20 = get_sma(symbol)
                    if last_check_price != 0 and current_price < last_check_price and current_price < sma_20:
                        if usdt_balance > 5.0:
                            qty = round(usdt_balance / current_price, 4)
                            print(f"📉 KAS BUYING @ {current_price}$")
                            exchange.create_market_buy_order(symbol, qty)
                    last_check_price = current_price
                    last_check_time = current_time
            else:
                my_trades = exchange.fetch_my_trades(symbol, limit=1)
                avg_cost = safe_float(my_trades[0]['price']) if my_trades else current_price
                target_sell_price = avg_cost * (1 + PROFIT_MARGIN)
                if current_price >= target_sell_price:
                    print(f"💰 KAS SELLING @ {current_price}$")
                    exchange.create_market_sell_order(symbol, asset_balance)
        except Exception as e: print(f"❌ KAS ERROR: {e}")
        
        time.sleep(10800) # فحص الحالة كل 3 ساعات

if __name__ == "__main__":
    run_kas_bot()
