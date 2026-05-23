import ccxt
import os
import time

# سحب المفاتيح من متغيرات النظام (Railway Variables)
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد الربط مع Bybit
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    target_profit = 1.0     
    trade_size_usdt = 20.0  
    
    print(f"🚀 بوت الربح الثابت يعمل الآن على {symbol} (فحص كل 3 ساعات)...")
    
    bought_amount = 0
    last_buy_price = 0

    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker.get('last')
            
            if current_price is None:
                continue

            if bought_amount == 0:
                print(f"🔎 السعر الحالي: {current_price:.5f} | يبحث عن فرصة شراء...")
                
                order = exchange.create_market_buy_order(symbol, trade_size_usdt / current_price)
                bought_amount = float(order['amount'])
                last_buy_price = float(order['average']) if 'average' in order else current_price
                print(f"✅ تم الشراء: {bought_amount:.4f} KAS بسعر {last_buy_price:.5f}")

            else:
                sell_price_target = last_buy_price + (target_profit / bought_amount)
                print(f"📈 السعر: {current_price:.5f} | هدف البيع: {sell_price_target:.5f}")
                
                if current_price >= sell_price_target:
                    print(f"🎯 السعر وصل للهدف! جاري البيع...")
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"💰 تم جني ربح 1 دولار!")
                    bought_amount = 0 
            
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            
        # زمن الانتظار: 10800 ثانية = 3 ساعات
        time.sleep(10800)

if __name__ == "__main__":
    if not api_key or not api_secret:
        print("❌ خطأ: يرجى التأكد من إضافة المفاتيح في Railway Variables!")
    else:
        run_trading_bot()
