import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد المنصة للوصول المباشر للحساب الموحد V5
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'unified'
    }
})

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
    TRADE_PERCENTAGE = 0.20       # حجم الصفقة = 20% من الرصيد المتاح (تكبر مع الأرباح)
    TARGET_PROFIT_USDT = 2.0      # الربح المستهدف الصافي بالدولار
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل البوت المطور بنظام الحساب الموحد V5 الصارم..")

    while True:
        try:
            # استدعاء الأرصدة مباشرة من الـ API الخاص بـ V5 للحساب الموحد
            unified_balance = exchange.privateGetV5AccountWalletBalance({
                'accountType': 'UNIFIED'
            })
            
            actual_usdt = 0.0
            actual_kas_in_wallet = 0.0
            
            # تفكيك البيانات القادمة من المنصة لاستخراج الأرصدة الحقيقية بدقة
            if 'result' in unified_balance and 'list' in unified_balance['result']:
                account_list = unified_balance['result']['list']
                if account_list:
                    # جلب القيمة الإجمالية للحساب بالدولار كخط دفاع بديل
                    total_equity = safe_float(account_list[0].get('totalEquity', 0.0))
                    
                    if 'coin' in account_list[0]:
                        for coin_data in account_list[0]['coin']:
                            if coin_data.get('coin') == 'USDT':
                                # التعديل الجوهري: قراءة الرصيد المتاح للتداول الفعلي وليس الجامد
                                actual_usdt = safe_float(coin_data.get('availableToWithdraw'))
                                if actual_usdt == 0.0:
                                    actual_usdt = safe_float(coin_data.get('walletBalance'))
                            elif coin_data.get('coin') == coin:
                                actual_kas_in_wallet = safe_float(coin_data.get('walletBalance'))
                    
                    # إذا قرأت المنصة صفر للكاش الحر بينما القيمة الإجمالية للمحفظة بها رصيد، نعتمد القيمة الإجمالية ليعمل البوت
                    if actual_usdt == 0.0 and 0.0 < total_equity <= MAX_ALLOWED_BALANCE:
                        actual_usdt = total_equity

            print(f"📊 قراءة الحساب الموحد الفورية -> الرصيد المتاح: {actual_usdt:.2f}$ | رصيد كاسبا: {actual_kas_in_wallet:.2f} KAS")

            # 🛠️ التعديل هنا: تحويل الرصيد إلى رقم صحيح int() لتجاهل أي كسور خفية بعد النقطة تماماً
            if int(actual_usdt) > int(MAX_ALLOWED_BALANCE):
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
            last_buy_price = price
            try:
                trades = exchange.fetch_my_trades(symbol, limit=5)
                if trades:
                    for t in reversed(trades):
                        if t.get('side') == 'buy' and t.get('price') is not None:
                            last_buy_price = safe_float(t.get('price'))
                            break
            except Exception as trade_error:
                print(f"⚠️ تنبيه أثناء جلب الصفقات السابقة: {trade_error} (سيتم استخدام السعر الحالي كمرجع)")

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
                    print("🎰 السيولة المتاحة غير كافية لفتح صفقة جديدة حالياً.")
            
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
                        print("⚠️ تفعيل أمر وقف الخسارة الفوري لحماية المحفظة الفورية من الهبوط المتتالي...")
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("⚠️ تم تأمين الحساب والخروج بنجاح.")

        except Exception as e:
            print(f"❌ خطأ في التنفيذ أو قراءة البيانات: {e}")
            
        print("-------------------------------------------------------------------------")
        time.sleep(10800) # فحص دوري دائم وصارم كل 3 ساعات دون انقطاع

if __name__ == "__main__":
    run_trading_bot()
