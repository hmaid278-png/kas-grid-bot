import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    coin = 'KAS'
    
    # تثبيت الميزانية على 200 دولار وتوزيعها على 5 صفقات
    total_budget_usdt = 200.0  
    trade_size_usdt = 40.0     # حجم الصفقة الواحدة (40$)
    target_profit = 2.0        # الربح المستهدف بالدولار عند البيع
    
    min_price = 0.0300
    max_price = 0.0633
    
    print(f"🚀 بوت الميزانية المثبتة ({total_budget_usdt}$) يعمل الآن...")

    while True:
        try:
            # 1. قراءة رصيد المحفظة الفعلي لمعرفة حالة السوق
            balance = exchange.fetch_balance()
            actual_kas_in_wallet = float(balance
