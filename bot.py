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
            
            # جلب كمية عملة KAS المتاحة فعلياً في المحفظة
            raw_kas = balance.get(coin, {})
            actual_kas_in_wallet = float(raw_kas.get('free', raw_kas.get('total', 0.0)))
            if actual_kas_in_wallet is None:
                actual_kas_in_wallet = 0.0

            print(f"📊 الرصيد الحالي المتاح في الحساب: {actual_usdt:.2f}$ | الرصيد الحالي من كاسبا: {actual_kas_in_wallet:.2f} KAS")

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

            # حساب حجم الصفقة الديناميكي بناءً على الرصيد الحالي المتاح
            dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
            if dynamic_trade_size > 40.0 and actual_usdt <= 200.0:
                pass 
            elif dynamic_trade_size > 40.0:
                dynamic_trade_size = 40.0

            # جلب آخر سعر شراء احتياطياً من المنصة لتحديد الأهداف بدقة
            trades = exchange.fetch_my_trades(symbol, limit=5)
            last_buy_price = price # قيمة افتراضية في حال فشل السجل
            
            if trades:
                for t in reversed(trades):
                    if t.get('side') == 'buy' and t.get('price') is not None:
                        last_buy_price = float(t['price'])
                        break

            # فحص ما إذا كان البوت يملك صفقة شراء مفتوحة بناءً على وجود كمية كاسبا توازي الصفقة
            # إذا كانت القيمة المتاحة بالدولار لكاسبا في المحفظة أقل من 5 دولار، نعتبر المحفظة جاهزة للشراء
            if (actual_kas_in_wallet * price) < 5.0:
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🔎 الرصيد مطابق للشروط. حجم الصفقة المحدث (تكبير تلقائي): {dynamic_trade_size:.2f}$")
                        print(f"🛒 تنفيذ أمر شراء عند السعر الحالي: {price:.5f}...")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء التراكمي بنجاح!")
                    else:
                        print(f"⚠️ السعر {price:.5f} خارج النطاق السعري المسموح. انتظار...")
                else:
                    print("🎰 الرصيد المتاح غير كافٍ لفتح صفقة جديدة بناءً على الحسبة التراكمية.")
            
            # حالة 2: هناك صفقة مفتوحة بالفعل ويجب مراقبتها (حماية السطر 96)
            else:
                # حساب الأهداف بأمان تام وتجنب القسمة على صفر أو استخدام قيم None
                current_qty = actual_kas_in_wallet
                if current_qty > 0:
                    sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / current_qty)
                    stop_loss_price = last_buy_price * 0.95
                    
                    print(f"⚙️ يراقب صفقة مستثمرة حالية | كمية المحفظة الحالية: {current_qty:.2f} KAS")
                    print(f"📊 السعر الحالي: {price:.5f} | هدف البيع: {sell_price_target:.5f} | وقف الخسارة: {stop_loss_price:.5f}")
                    
                    if price >= sell_price_target:
                        print("💰 السعر ضرب الهدف المستهدف! بيع الكمية بالكامل...")
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("✅ تم جني الربح وإعادة إدخاله في سيولة الحساب للتكبير القادم!")
                    elif price <= stop_loss_price:
                        print("⚠️ تفعيل وقف الخسارة لحماية المحفظة المخصصة...")
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("⚠️ تم الخروج من الصفقة بنجاح.")
                else:
                    print("⚠️ تضارب في قراءة كميات المحفظة، سيتم إعادة الفحص الدورة القادمة.")

        except Exception as e:
