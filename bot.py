import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    min_price = 0.0300
    max_price = 0.0633
    target_profit = 2.0      # الربح المستهدف 2 دولار
    trade_size_usdt = 40.0   # قيمة الصفقة الواحدة (تقسيم الـ 200 دولار إلى 5 مراحل)
    
    print(f"🚀 بوت 200$ يعمل الآن على {symbol} ضمن نطاق ({min_price} - {max_price})...")
    
    bought_amount = 0
    last_buy_price = 0

    while True:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker.get('last')
            
            if price is None or not (min_price <= price <= max_price):
                time.sleep(10800) # انتظار 3 ساعات إذا كان خارج النطاق
                continue

            # حالة: البوت لا يملك عملات (جاهز للشراء)
            if bought_amount == 0:
                print(f"🔎 السعر {price:.5f} داخل النطاق، شراء بـ {trade_size_usdt}$...")
                order = exchange.create_market_buy_order(symbol, trade_size_usdt / price)
                bought_amount = float(order['amount'])
                last_buy_price = float(order['average']) if 'average' in order else price
                print(f"✅ تم الشراء: {bought_amount:.4f} KAS")

            # حالة: البوت يملك عملات (يراقب الهدف ووقف الخسارة)
            else:
                sell_price_target = last_buy_price + (target_profit / bought_amount)
                stop_loss_price = last_buy_price * 0.95 # وقف خسارة عند انخفاض 5%
                
                print(f"📈 السعر الحالي: {price:.5f} | هدف الربح: {sell_price_target:.5f} | وقف الخسارة: {stop_loss_price:.5f}")
                
                # تنفيذ جني الربح
                if price >= sell_price_target:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"💰 تم جني ربح 2 دولار بنجاح!")
                    bought_amount = 0 
                
                # تنفيذ وقف الخسارة
                elif price <= stop_loss_price:
                    exchange.create_market_sell_order(symbol, bought_amount)
                    print(f"⚠️ انخفاض حاد! تم تفعيل وقف الخسارة لحماية المحفظة.")
                    bought_amount = 0 
            
        except Exception as e:
            print(f"⚠️ خطأ: {e}")
            
        time.sleep(10800) # فحص كل 3 ساعات

if __name__ == "__main__":
    run_trading_bot()
