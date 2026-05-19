import ccxt
import time

# --- 1. إعدادات الحساب ---
API_KEY = "ضع_مفتاحك_هنا"
API_SECRET = "ضع_سرك_هنا"
SYMBOL = "KAS/USDT"  # تأكد من إضافة علامة /

# --- 2. إعدادات الشبكة (Grid) ---
INVESTMENT = 100       # مبلغ 100 دولار
GRID_COUNT = 5         # 5 خطوط تداول
SPREAD = 0.02          # مسافة 2% بين كل خط

exchange = ccxt.bybit({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def start_bot():
    print("Bot is active and monitoring KAS market...")
    while True:
        try:
            # جلب السعر الحالي
            ticker = exchange.fetch_ticker(SYMBOL)
            price = ticker['last']
            
            # منطق بسيط: وضع أوامر شراء تحت السعر الحالي
            buy_price = price * (1 - SPREAD)
            amount = (INVESTMENT / GRID_COUNT) / buy_price
            
            print(f"Current Price: {price}. Placing buy order at {buy_price}")
            
            # تنفيذ الشراء
            # exchange.create_limit_buy_order(SYMBOL, amount, buy_price)
            
            # ملاحظة: سطر الشراء أعلاه معطل حالياً (مسبوق بـ #) 
            # لإزالة الـ # سيبدأ البوت بالشراء فعلياً
            
            time.sleep(300) # يكرر العملية كل 5 دقائق
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    start_bot()
