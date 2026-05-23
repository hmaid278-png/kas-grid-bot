import ccxt
import os
import time

# النظام سيقوم بسحب الرموز من إعدادات Railway Variables تلقائياً
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد الربط مع Bybit
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

def get_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker.get('last')
    except Exception as e:
        print(f"خطأ في جلب السعر: {e}")
        return None

def run_bot():
    symbol = 'BTC/USDT'  # يمكنك تغيير الزوج هنا
    print(f"🚀 البوت بدأ العمل على زوج {symbol}...")
    
    while True:
        price = get_price(symbol)
        
        # فحص آمن: نتحقق أن السعر موجود قبل عرضه لتجنب انهيار البوت
        if price is not None:
            print(f"📈 السعر الحالي لـ {symbol} هو: {price:.2f}")
        else:
            print("⚠️ تعذر جلب السعر، محاولة أخرى بعد 10 ثواني...")
            
        time.sleep(10)

if __name__ == "__main__":
    # فحص أولي: هل وجد النظام المفاتيح في ريلوي؟
    if not api_key or not api_secret:
        print("❌ خطأ: يرجى التأكد من إضافة BYBIT_API_KEY و BYBIT_API_SECRET في Railway Variables!")
    else:
        run_bot()
