import ccxt
import time
import schedule
import os

# استخدام المتغيرات البيئية لزيادة الأمان (بدل وضع المفاتيح داخل الكود)
API_KEY = os.environ.get("AVKLVzE3M9dEaQ8WoY")
API_SECRET = os.environ.get("d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel")
SYMBOL = "KAS/USDT"

# تهيئة المنصة
exchange = ccxt.bybit({
    'apiKey': API_KEY, 
    'secret': API_SECRET, 
    'enableRateLimit': True, 
    'options': {'defaultType': 'spot'}
})

def execute_trading_job():
    print(f"[{time.strftime('%H:%M:%S')}] استيقظت لتفقد السوق...")
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker['last']
        print(f"سعر كاسبا الحالي: {price}")
        # هنا ستضع أوامر الشراء والبيع لاحقاً
    except Exception as e:
        print(f"خطأ: {e}")

# جدولة المهام (3 مرات يومياً)
schedule.every().day.at("08:00").do(execute_trading_job)
schedule.every().day.at("14:00").do(execute_trading_job)
schedule.every().day.at("20:00").do(execute_trading_job)

print("البوت يعمل الآن بنظام الـ Worker...")

# الحلقة التي تمنع البوت من الإغلاق
while True:
    schedule.run_pending()
    time.sleep(60)
