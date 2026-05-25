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
                        last

