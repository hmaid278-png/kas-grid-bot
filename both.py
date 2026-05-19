import ccxt
import time
import schedule
import os
import sys

# إعدادات الأمان: سحب المفاتيح من متغيرات النظام في Railway
API_KEY = os.environ.get("AVKLVzE3M9dEaQ8WoY")
API_SECRET = os.environ.get("d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel")
SYMBOL = "KAS/USDT"

# تهيئة المنصة
try:
    exchange = ccxt.bybit({
        'apiKey': API_KEY, 
        'secret': API_SECRET, 
        'enableRateLimit': True, 
        'options': {'defaultType': 'spot'}
    })
except Exception as e:
    print(f"خطأ في تهيئة المنصة: {e}")
    sys.exit(1)

def execute_trading_job():
    print(f"[{time.strftime('%H:%M:%S')}] البوت يعمل - استيقظت لتفقد السوق...")
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker['last']
        print(f"سعر كاسبا الحالي: {price}")
        
        # هنا سيتم وضع منطق الشراء والبيع لاحقاً
        
        print("انتهت المهمة بنجاح، سأعود للنوم.")
    except Exception as e:
        print(f"حدث خطأ أثناء تفقد السوق: {e}")

# جدولة المهام (3 مرات يومياً)
schedule.every().day.at("08:00").do(execute_trading_job)
schedule.every().day.at("14:00").do(execute_trading_job)
schedule.every().day.at("20:00").do(execute_trading_job)

print("البوت جاهز ويعمل الآن في الخلفية (Worker)...")

# الحلقة الرئيسية مع معالجة الأخطاء (صمام الأمان)
while True:
    try:
        schedule.run_pending()
        time.sleep(60) # راحة لمدة دقيقة
    except Exception as e:
        print(f"خطأ غير متوقع في الحلقة الرئيسية: {e}")
        time.sleep(60) # انتظار ثم المحاولة مجدداً
