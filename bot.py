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

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def run_trading_bot():
    symbol = 'KAS/USDT' 
    # تم تعديل نسبة الربح لتصبح 2%
    PROFIT_MARGIN = 0.02   
    
    print("🚀 KAS BOT ACTIVATED | 2.0% PROFIT | 15 MIN INTERVAL")

    while True:
        try:
            balance = exchange.fetch_balance()
            usdt_balance = safe_float(balance['total']['USDT'])
            kas_balance = safe_float(balance['total']['KAS'])
            
            ticker = exchange.fetch_ticker(symbol)
            price = safe_float(ticker.get('last'))
            
            # الشراء بكامل الرصيد (إعادة استثمار تراكمية)
            if kas_balance * price < 5.0: 
                amount_to_invest = usdt_balance
                if amount_to_invest > 5.0:
                    qty = round(amount_to_invest / price, 4)
                    print(f"🛒 BUYING {qty} KAS @ {price}$")
                    exchange.create_market_buy_order(symbol, qty)
            
            # المراقبة لهدف 2%
            else:
                target_sell_price = price * (1 + PROFIT_MARGIN)
                print(f"⚙️ MONITORING KAS | TARGET: {target_sell_price:.2f}$")
                
                if price >= target_sell_price:
                    print("💰 TARGET REACHED! SELLING...")
                    exchange.create_market_sell_order(symbol, kas_balance)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        # فحص كل 15 دقيقة
        time.sleep(900) 

if __name__ == "__main__":
    run_trading_bot()
