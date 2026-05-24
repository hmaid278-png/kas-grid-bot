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
    coin = 'KAS'
    
    # تثبيت الميزانية على 200 دولار وتوزيعها على 5 صفقات
    total_budget_usdt = 200.0  
    trade_size_usdt = 40.0     # حجم الصفقة الواحدة (40$)
    target_profit = 2.0        # الربح المستهدف بالدولار عند البيع
    
    min_price = 0.0300
    max_price = 0.0633
    
    print("🚀 بوت الميزانية المثبتة (200$) يعمل الآن...")

    while True:
        try:
            # 1. قراءة رصيد المحفظة الفعلي لمعرفة حالة السوق
            balance = exchange.fetch_balance()
            actual_kas_in_wallet = float(balance['total'].get(coin, 0))
            
            ticker = exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                time.sleep(60)
                continue
            price = float(ticker['last'])

            # حالة 1: المحفظة فارغة من العملة (أقل من 10 حبات) -> شراء بـ 40$
            if actual_kas_in_wallet < 10:  
                if min_price <= price <= max_price:
                    print(f"🔎 المحفظة جاهزة. السعر {price:.5f} | شراء بـ {trade_size_usdt}$...")
                    exchange.create_market_buy_order(symbol, trade_size_usdt / price)
                    print("✅ تم الشراء بنجاح!")
                else:
                    print(f"⚠️ السعر {price:.5f} خارج النطاق السعري المحدد. انتظار...")
            
            # حالة 2: العملة موجودة -> إدارة الـ 200$ المخصصة فقط
            else:
                # جلب سعر آخر عملية شراء من سجل المنصة
                trades = exchange.fetch_my_trades(symbol, limit=10)
                last_buy_price = price
                for t in reversed(trades):
                    if t['side'] == 'buy':
                        last_buy_price = float(t['price'])
                        break

                # حساب كمية الكاسبا التي تعادل ميزانية الـ 200$ فقط بناءً على السعر
                controlled_kas_amount = total_budget_usdt / last_buy_price
                
                # أمان: إذا كان المتاح فعلياً في المحفظة أقل من الكمية المحسوبة، نأخذ المتاح
                if actual_kas_in_wallet < controlled_kas_amount:
                    controlled_kas_amount = actual_kas_in_wallet

                # حساب هدف البيع (الخروج بربح 2 دولار فوق الـ 200$)
                sell_price_target = last_buy_price + (target_profit / controlled_kas_amount)
                stop_loss_price = last_buy_price * 0.95
                
                print(f"⚙️ نتحكم بـ {controlled_kas_amount:.2f} KAS (ميزانية 200$) | إجمالي المحفظة: {actual_kas_in_wallet:.2f}")
                print(f"📊 السعر الحالي: {price:.5f} | هدف البيع: {sell_price_target:.5f}")
                
                # تنفيذ الشروط للكمية المحددة فقط
                if price >= sell_price_target:
                    print("💰 السعر وصل للهدف! بيع كمية الميزانية المحددة...")
                    exchange.create_market_sell_order(symbol, controlled_kas_amount)
                    print("✅ تم جني الربح بنجاح!")
                elif price <= stop_loss_price:
                    print("⚠️ تفعيل وقف الخسارة لحماية الـ 200$...")
                    exchange.create_market_sell_order(symbol, controlled_kas_amount)
                    print("⚠️ تم الخروج لحماية رأس المال.")

        except Exception as e:
            print(f"❌ خطأ تقني: {e}")
            
        time.sleep(10800) # فحص متكرر مستمر كل 3 ساعات دائم ودون توقف

if __name__ == "__main__":
    run_trading_bot()
