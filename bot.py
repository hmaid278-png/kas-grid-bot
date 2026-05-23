import ccxt
import os
import time

# سحب المفاتيح من متغيرات النظام (Railway Variables)
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد الربط مع Bybit للعمل بنظام Spot
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'} 
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    max_total_budget = 180.0    # سقف الميزانية الصارم
    trade_size_usdt = 36.0      # قيمة الصفقة الواحدة (180 / 5 = 36)
    target_profit = 2.0         # الربح المستهدف بالدولار
    
    # نطاق التداول
    min_price = 0.0300
    max_price = 0.0633
    
    print(f"🚀 البوت يعمل الآن على {symbol} بميزانية 180$...")
    
    bought_amount = 0
    last_buy_price = 0

    while True:
        try:
            # جلب آخر سعر
            ticker = exchange.fetch_ticker(symbol)
            price = ticker.get('last')
            
            if price is None:
                time.sleep(60)
                continue

            # مراقبة نطاق التداول
            if not (min_price <= price <= max_price):
                print(f"⚠️ السعر الحالي {price:.5f} خارج نطاق العمل. انتظار...")
                time.sleep(10800)
                continue

            # حالة الشراء
            if bought_amount == 0:
                print(f"🔎 السعر {price:.5f} داخل النطاق، شراء بـ {trade_size_usdt}$...")
                order = exchange.create_market_buy_order(symbol, trade_size_usdt / price)
                bought_amount = float(order.get('amount', 0))
                last_buy_price = float(order.get('average', price))
                print(f"✅ تم الشراء بنجاح! الكمية: {bought_amount:.4f}")

            # حالة البيع (جني الربح أو وقف الخسارة)
            else:
                sell_price_target = last_buy_price + (target_profit / bought_amount)
                stop_loss_price = last_buy_price * 0.95
                
                print(f"📈 السعر الحالي: {price:.5f} | هدف الربح: {sell_price_target:.5f}")
                
                if price >= sell_price_target:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"💰 تم جني ربح 2 دولار بنجاح!")
                    bought_amount = 0 
                
                elif price <= stop_loss_price:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"⚠️ انخفاض حاد! تفعيل وقف الخسارة.")
                    bought_amount = 0 
            
        except Exception as e:
            print(f"❌ خطأ أثناء التداول: {e}")
            
        time.sleep(10800) # فحص كل 3 ساعات

if __name__ == "__main__":
    run_trading_bot()
