import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    max_total_budget = 180.0
    trade_size_usdt = 36.0
    target_profit = 2.0
    min_price = 0.0300
    max_price = 0.0633
    
    print(f"🚀 بوت 180$ يعمل الآن على {symbol}...")
    
    bought_amount = 0
    last_buy_price = 0

    while True:
        try:
            # استخدام fetch_ticker بشكل آمن
            ticker = exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker or ticker['last'] is None:
                print("⚠️ تعذر الحصول على السعر، إعادة المحاولة...")
                time.sleep(60)
                continue
                
            price = float(ticker['last'])
            
            # مراقبة نطاق التداول
            if not (min_price <= price <= max_price):
                print(f"⚠️ السعر الحالي {price:.5f} خارج النطاق. انتظار...")
                time.sleep(3600)
                continue

            # حالة الشراء
            if bought_amount == 0:
                print(f"🔎 السعر {price:.5f} | شراء بـ {trade_size_usdt}$...")
                order = exchange.create_market_buy_order(symbol, trade_size_usdt / price)
                
                # التحقق من أن الطلب عاد ببيانات
                if order and 'amount' in order:
                    bought_amount = float(order['amount'])
                    last_buy_price = float(order.get('average', price))
                    print(f"✅ تم الشراء بنجاح! الكمية: {bought_amount:.4f}")
                else:
                    print("❌ فشل تنفيذ أمر الشراء.")

            # حالة المراقبة والبيع
            else:
                sell_price_target = last_buy_price + (target_profit / bought_amount)
                stop_loss_price = last_buy_price * 0.95
                
                print(f"📈 السعر الحالي: {price:.5f} | هدف الربح: {sell_price_target:.5f}")
                
                if price >= sell_price_target:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"💰 تم جني ربح 2 دولار!")
                    bought_amount = 0 
                
                elif price <= stop_loss_price:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"⚠️ انخفاض حاد! تفعيل وقف الخسارة.")
                    bought_amount = 0 
            
        except Exception as e:
            print(f"❌ خطأ تقني: {e}")
            
        time.sleep(10800) 

if __name__ == "__main__":
    run_trading_bot()
