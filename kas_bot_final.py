"""
KAS Grid Bot - Professional CCXT Version
"""
import os
import time
import logging
import ccxt
import pandas as pd

# 1. نظام سجلات تفصيلي (Logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# 2. حماية البيانات الحساسة (Environment Variables)
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

if not API_KEY or not API_SECRET:
    log.error("❌ مفاتيح API مفقودة! تأكد من إضافتها في Railway Variables.")
    exit(1)

# 3. الاعتماد على مكتبات عالمية & احترام حدود المنصة (Rate Limits)
exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True, # تفعيل المؤقتات الذكية لتجنب الحظر
    'options': {
        'defaultType': 'spot' # التداول الفوري
    }
})

# إعدادات الشبكة وإدارة المخاطر
SYMBOL = "KAS/USDT" # صيغة ccxt المعتمدة
GRID_LOWER = 0.034
GRID_UPPER = 0.060
GRID_STEP = 0.002
CAPITAL = 100.0

def run_bot():
    log.info("🚀 بدء تشغيل KAS Grid Bot (النسخة الاحترافية)...")
    
    while True:
        try:
            # جلب السعر والرصيد باستخدام ccxt
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']
            
            balance = exchange.fetch_balance()
            usdt_free = balance['USDT']['free'] if 'USDT' in balance else 0.0
            kas_free = balance['KAS']['free'] if 'KAS' in balance else 0.0
            
            log.info("-" * 40)
            log.info(f"📈 سعر KAS الحالي: ${current_price}")
            log.info(f"💰 الرصيد المتاح: {usdt_free:.2f} USDT | {kas_free:.2f} KAS")
            
            # هنا سيتم وضع أوامر الشراء والبيع (سنقوم بتفعيلها بعد التأكد من الاتصال)
            # مثال لآلية الشراء المستقبلية (إدارة المخاطر الصارمة):
            # order = exchange.create_limit_buy_order(SYMBOL, amount, price)
            
            # الاستهلاك الاقتصادي للموارد: سكون بين الدورات
            log.info("⏳ انتظار الدورة القادمة لتوفير الموارد...")
            time.sleep(3600) # فحص كل ساعة

        # 4. المعالجة التلقائية للأخطاء (بدون تدخل عاطفي أو انهيار)
        except ccxt.NetworkError as e:
            log.warning(f"⚠️ انقطاع في الشبكة، سيتم المحاولة بعد دقيقة... التفاصيل: {e}")
            time.sleep(60)
        except ccxt.ExchangeError as e:
            log.error(f"❌ خطأ من منصة Bybit: {e}")
            time.sleep(60)
        except Exception as e:
            log.error(f"❌ خطأ غير متوقع، البوت يعيد ضبط نفسه... {e}")
            time.sleep(120)

if __name__ == "__main__":
    run_bot()
