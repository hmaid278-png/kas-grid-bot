import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد المنصة للوصول المباشر للحساب الموحد
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'unified'  # فرض القراءة من الحساب الموحد
    }
})

# دالة أمان لمنع خطأ NoneType وتحويل البيانات لأرقام
def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def run_trading_bot():
    symbol = 'KAS/USDT'
    coin = 'KAS'
    
    # --- إعدادات رأس المال وإعادة الاستثمار ---
    MAX_ALLOWED_BALANCE = 200.0   # البوت يعمل فقط إذا كان الرصيد المتاح 200$ فما دون
    TRADE_PERCENTAGE = 0.20       # حجم الصفقة = 20% من الرصيد المتاح (يكبر مع الأرباح)
    TARGET_PROFIT_USDT = 2.0      # الربح المستهدف الصافي بالدولار
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل البوت المطور بنظام الحساب الموحد وقاطع الأخطاء الفنيّة..")

    while True:
        try:
            # جلب الرصيد الإجمالي والمتاح بنظام الحساب الموحد الصارم
            balance = exchange.fetch_balance()
            
            # محاولة جلب رصيد USDT من كل المسارات الممكنة للحساب الموحد (free أو total أو الجلب المباشر)
            usdt_info = balance.get('USDT', {})
            actual_usdt = safe_float(usdt_info.get('free', usdt_info.get('total', 0.0)))
            
            # إذا أعادت المكتبة صفر بسبب الهيكلة، نجبر الكود على البحث في رصيد الحساب الموحد الإجمالي
            if actual_usdt == 0.0 and 'unified' in balance:
                actual_usdt = safe_float(balance['unified'].get('USDT', 0.0))
            
            # جلب رصيد عملة كاسبا الفعلي بنفس الطريقة الآمنة
            kas_info = balance.get(coin, {})
            actual_kas_in_wallet = safe_float(kas_info.get('free', kas_info.get('total', 0.0)))
            
            print(f"📊 قراءة الحساب الموحد الفورية -> الرصيد المتاح: {actual_usdt:.2f}$ | رصيد كاسبا: {actual_kas_in_wallet:.2f} KAS")

            # شرط الأمان لحماية بقية محفظتك (الـ 400 دولار الأخرى)
            if actual_usdt > MAX_ALLOWED_BALANCE:
                print(f"🛑 حظر تلقائي: الرصيد الحالي ({actual_usdt:.2f}$) أكبر من 200$. تم إيقاف الفحص لحماية أموالك.")
                print("-------------------------------------------------------------------------")
                time.sleep(10800)
                continue

            ticker = exchange.fetch_ticker(symbol)
            if not ticker or ticker.get('last') is None:
                time.sleep(60)
                continue
                
            price = safe_float(ticker.get('last'))
            if price == 0.0:
                time.sleep(60)
                continue

            # حساب حجم الصفقة التراكمي (يكبر تلقائياً كلما زادت الأرباح)
            dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
            if dynamic_trade_size > 40.0 and actual_usdt <= 200.0:
                pass 
            elif dynamic_trade_size > 40.0:
                dynamic_trade_size = 40.0

            # جلب آخر سعر شراء بأمان تام لتحديد الأهداف بدقة
            trades = exchange.fetch_my_trades(symbol, limit=5)
            last_buy_price = price 
            
            if trades:
                for t in reversed(trades):
                    if t.get('side') == 'buy' and t.get('price') is not None:
                        last_buy_price = safe_float(t.get('price'))
                        break

            # حالة 1: تنفيذ أمر الشراء التراكمي (إذا لم يكن هناك صفقات مفتوحة)
            if (actual_kas_in_wallet * price) < 5.0:
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🔎 الرصيد مطابق ومسموح تداوله. حجم صفقتك النامية: {dynamic_trade_size:.2f}$")
                        print(f"🛒 إرسال أمر شراء ماركت لـ KAS عند السعر: {price:.5f}")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء بنجاح وجاري بدء المراقبة لتأمين الربح!")
                    else:
                        print(f"⚠️ السعر الحالي {price:.5f} خارج النطاق المسموح لبوت الشراء.")
                else:
                    print("🎰 السيولة المتاحة في نطاق الـ 200$ غير كافية لفتح صفقة جديدة حالياً.")
            
            # حالة 2: مراقبة صفقة الشراء الحالية واقتناص أهداف البيع والأرباح
            else:
                current_qty = actual_kas_in_wallet
                if current_qty > 0:
                    sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / current_qty)
                    stop_loss_price = last_buy_price * 0.95
                    
                    print(f"⚙️ يراقب صفقة قائمة ومحمية بالكامل | كمية العقد: {current_qty:.2f} KAS")
                    print(f"📊 السعر الآن: {price:.5f} | هدف البيع التراكمي: {sell_price_target:.5f} | وقف الخسارة: {stop_loss_price:.5f}")
                    
                    if price >= sell_price_target:
                        print("💰 وصل السعر للهدف المخطط له! بيع كامل صفقة الأرباح الآن...")
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("✅ تم جني الأرباح وضمها للكاش المتاح لتدويرها تلقائياً بالصفقة القادمة!")
                    elif price <= stop_loss_price:
                        print("⚠️ تفعيل أمر وقف الخسارة الفوري لحماية الحساب من الهبوط المتتالي...")
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("⚠️ تم تأمين الحساب والخروج بنجاح.")

        except Exception as e:
            print(f"❌ خطأ في التنفيذ أو قراءة البيانات: {e}")
            
        print("-------------------------------------------------------------------------")
        time.sleep(10800) # فحص مستمر وثابت كل 3 ساعات بدون توقف

if __name__ == "__main__":
    run_trading_bot()
