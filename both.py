import ccxt
import time
import schedule
import os
import sys

# --- 1. الإعدادات ---
# تأكد من إضافة API_KEY و API_SECRET في تبويب Variables داخل Railway
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

# --- 2. وظيفة التداول ---
def execute_trading_job():
    print(f"[{time.strftime('%H:%M:%S')}] استيقظت لتفقد السوق (جدولة 3 ساعات)...")
    try:
        ticker = exchange.fetch_ticker(SYMBOL)
        price = ticker['last']
        print(f"سعر كاسبا الحالي: {price}")
        # هنا ستضع أوامر الشراء والبيع لاحقاً
    except Exception as e:
        print(f"خطأ أثناء تفقد السوق: {e}")

# --- 3. الجدولة (كل 3 ساعات) ---
schedule.every(3).hours.do(execute_trading_job)

# --- 4. الحلقة الرئيسية (صمام الأمان) ---
print("البوت يعمل الآن بنظام الـ Worker (جدولة كل 3 ساعات)...")

while True:
    try:
        # تشغيل المهام المجدولة
        schedule.run_pending()
        
        # النوم لمدة 10 دقائق بين كل فحص وآخر للحفاظ على استهلاك المعالج
        # هذا يمنع البوت من أن يُصنف كـ "ميت" ويحمي رصيدك
        time.sleep(600) 
        
    except Exception as e:
        print(f"خطأ غير متوقع في الحلقة الرئيسية: {e}")
        time.sleep(600)
