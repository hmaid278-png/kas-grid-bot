import os
import time
import logging
import ccxt

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# إعدادات الاتصال
exchange = ccxt.bybit({
    'apiKey': os.getenv('AVKLVzE3M9dEaQ8WoY'),
    'secret': os.getenv('d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel'),
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

SYMBOL = 'KAS/USDT'
LOWER_BOUND = 0.034  # القاع
UPPER_BOUND = 0.060  # القمة
STEP = 0.002         # الفارق
ORDER_VALUE = 15.0   # قيمة الصفقة بالدولار

def run_bot():
    logging.info("بدء البوت بنظام النطاق الثابت (0.034 - 0.06)")
    
    while True:
        try:
            ticker = exchange.fetch_ticker(SYMBOL)
            current_price = ticker['last']
            logging.info(f"السعر الحالي: {current_price}")
            
            # التأكد من أن السعر داخل النطاق
            if LOWER_BOUND <= current_price <= UPPER_BOUND:
                # حساب مستويات الشراء والبيع بناءً على السعر الحالي
                # الشراء يكون تحت السعر الحالي، والبيع فوقه
                buy_price = round(current_price - STEP, 4)
                sell_price = round(current_price + STEP, 4)
                
                amount = ORDER_VALUE / current_price
                
                # وضع أوامر معلقة
                exchange.create_limit_buy_order(SYMBOL, amount, buy_price)
                exchange.create_limit_sell_order(SYMBOL, amount, sell_price)
                
                logging.info(f"تم وضع أمر شراء عند {buy_price} وبيع عند {sell_price}")
            else:
                logging.warning("السعر خارج النطاق المحدد (0.034 - 0.06). البوت ينتظر...")
                
        except Exception as e:
            logging.error(f"خطأ: {e}")
            
        time.sleep(3600) # انتظار ساعة قبل المحاولة التالية

if __name__ == '__main__':
    run_bot()
