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
    
    # --- إعدادات إعادة استثمار الأرباح والتكبير التلقائي ---
    MAX_ALLOWED_BALANCE = 200.0   # سقف الأمان للحساب (200$ فما دون)
    TRADE_PERCENTAGE = 0.20       # حجم الصفقة = 20% من الرصيد المتاح (تكبر مع الأرباح)
    TARGET_PROFIT_USDT = 2.0      # الربح المستهدف الصافي بالدولار عند البيع
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل بوت إعادة استثمار الأرباح التراكمي المستمر..")
    print(f"📈 حجم الصفقة سيكبر تلقائياً بنسبة 20% مع كل ربح يتحقق في المحفظة.")

    while True:
        try:
            # جلب الرصيد الفعلي من المنصة
            balance = exchange.fetch_balance()
            raw_usdt = balance.get('USDT', {})
            actual_usdt = raw_usdt.get('free', raw_usdt.get('total', 0.0))
            
            if actual_usdt is None:
                actual_usdt = 0.0
            else:
                actual_usdt = float(actual_usdt)
            
            print(f"📊 الرصيد الحالي المتاح في الحساب: {actual_usdt:.2f}$")

            # الحماية الصارمة: إذا تجاوز الرصيد المتاح 200 دولار، يتوقف البوت لحماية المحفظة
            if actual_usdt > MAX_ALLOWED_BALANCE:
                print(f"🛑 حظر تلقائي: الرصيد المتاح ({actual_usdt:.2f}$) أكبر من 200$. تم إيقاف العمل لحماية الـ 400$ الأخرى.")
                print("-------------------------------------------------------------------------")
                time.sleep(10800)
                continue

            ticker = exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                time.sleep(60)
                continue
            price = float(ticker['last'])

            # جلب آخر عملية شراء قام بها البوت لمعرفة السعر والكمية الدقيقة
            trades = exchange.fetch_my_trades(symbol, limit=5)
            last_buy_price = None
            bot_purchased_qty = None

            for t in reversed(trades):
                if t['side'] == 'buy':
                    if t.get('price') is not None and t.get('amount') is not None:
                        last_buy_price = float(t['price'])
                        bot_purchased_qty = float(t['amount'])
                        break

            # تحديد حالة السوق بناءً على آخر عملية ناجحة مسجلة
            last_trade_side = 'sell'
            if trades:
                for t in reversed(trades):
                    if t.get('side'):
                        last_trade_side = t['side']
                        break
            
            # حالة 1: الشراء (حجم ديناميكي يكبر مع الأرباح)
            if last_trade_side == 'sell' or bot_purchased_qty is None:
                # حساب حجم الصفقة الجديد بناءً على رصيد المحفظة الحالي (إعادة الاستثمار التراكمي)
                dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
                
                # تأمين: لضمان عدم تجاوز ميزانية الـ 200$ الأساسية في البداية
                if dynamic_trade_size > 40.0 and actual_usdt <= 200.0:
                    pass # السماح للحجم بالنمو إذا كان ناتجاً عن أرباح فعلية
                elif dynamic_trade_size > 40.0:
                    dynamic_trade_size = 40.0 # كبح الحجم لو كان الرصيد مرتفعاً لسبب خارجي

                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🔎 الرصيد مطابق للشروط. حجم الصفقة المحدث (تكبير تلقائي): {dynamic_trade_size:.2f}$")
                        print(f"🛒 تنفيذ أمر شراء عند السعر الحالي: {price:.5f}...")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء التراكمي بنجاح!")
                    else:
                        print(f"⚠️
