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
    
    print(f"🚀 KAS ACTIVE | COMPOUNDING GROWTH MODE")

    while True:
        try:
            balance = exchange.fetch_balance()
            usdt_balance = safe_float(balance['total']['USDT'])
            asset_balance = safe_float(balance['total'][asset_name])
            ticker = exchange.fetch_ticker(symbol)
            current_price = safe_float(ticker.get('last'))
            current_time = time.time()
            
            if asset_balance * current_price < 5.0:
                if current_time - last_check_time >= 28800:
                    sma_20 = get_sma(symbol)
                    if last_check_price != 0 and current_price < last_check_price and current_price < sma_20:
                        if usdt_balance > 10.0:
                            # إعادة استثمار 95% من الرصيد (أسلوب أسي)
                            buy_amount = (usdt_balance * 0.95) / current_price
                            print(f"📈 KAS COMPOUND BUY (95%) @ {current_price}$")
                            exchange.create_market_buy_order(symbol, buy_amount)
                    last_check_price = current_price
                    last_check_time = current_time
            else:
                my_trades = exchange.fetch_my_trades(symbol, limit=10)
                avg_cost = sum([t['price'] for t in my_trades if t['side'] == 'buy']) / len([t for t in my_trades if t['side'] == 'buy']) if my_trades else current_price
                target_sell_price = avg_cost * (1 + PROFIT_MARGIN)
                
                if current_price >= target_sell_price:
                    print(f"💰 KAS TARGET REACHED! SELLING ALL @ {current_price}$")
                    exchange.create_market_sell_order(symbol, asset_balance)
                    
        except Exception as e: print(f"❌ KAS ERROR: {e}")
        time.sleep(10800)

if __name__ == "__main__":
    run_kas_bot()
