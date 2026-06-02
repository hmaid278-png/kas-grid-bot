import ccxt
import os
import time

# إعداد الاتصال
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'unified'}
})

exchange.load_markets()

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def run_trading_bot():
    symbol = 'KAS/USDT'
    asset_name = 'KAS'
    PROFIT_MARGIN = 0.02   
    
    print(f"🚀 {asset_name} BOT ACTIVATED | 2.0% PROFIT | 15 MIN INTERVAL")

    while True:
        try:
            balance = exchange.fetch_balance()
            usdt_balance = safe_float(balance['total']['USDT'])
            asset_balance = safe_float(balance['total'][asset_name])
            
            ticker = exchange.fetch_ticker(symbol)
            last_price = safe_float(ticker.get('last'))
            
            # الشراء بكامل الرصيد إذا كان الرصيد من العملة أقل من 5 دولار
            if asset_balance * last_price < 5.0: 
                if usdt_balance > 5.0:
                    qty = round(usdt_balance / last_price, 4)
                    print(f"🛒 BUYING {qty} {asset_name} @ {last_price}$")
                    exchange.create_market_buy_order(symbol, qty)
            
            # المراقبة لهدف 2% بناءً على تكلفة الشراء الحقيقية
            else:
                my_trades = exchange.fetch_my_trades(symbol, limit=1)
                avg_cost = safe_float(my_trades[0]['price']) if my_trades else last_price
                target_sell_price = avg_cost * (1 + PROFIT_MARGIN)
                
                print(f"⚙️ MONITORING {asset_name} | COST: {avg_cost:.4f}$ | TARGET: {target_sell_price:.4f}$")
                
                if last_price >= target_sell_price:
                    print("💰 TARGET REACHED! SELLING...")
                    exchange.create_market_sell_order(symbol, asset_balance)

        except Exception as e:
            print(f"❌ ERROR in {asset_name}: {e}")
            
        time.sleep(900) 

if __name__ == "__main__":
    run_trading_bot()
