import ccxt
import os
import time

# سحب المفاتيح من متغيرات النظام (Railway Variables)
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد الربط مع Bybit
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
})

def run_trading_bot():
    symbol = 'KAS/USDT'
    budget = 100.0          # الميزانية الكلية
    target_profit = 1.0     # الربح المستهدف بالدولار لكل عملية
    trade_size_usdt = 20.0  # حجم الصفقة الواحدة (تقسيم الـ 100 دولار إلى 5 صفقات)
    
    print(f"🚀 بوت الربح الثابت (1$ لكل عملية) يعمل الآن على {symbol}...")
    
    # متغيرات لتتبع الصفقة الحالية
    bought_amount = 0
    last_buy_price = 0

    while True:
        try:
            # جلب آخر سعر
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker.get('last')
            
            if current_price is None:
                continue

            # حالة: البوت لا يملك عملات (جاهز للشراء)
            if bought_amount == 0:
                print(f"🔎 السعر الحالي: {current_price:.5f} | جاري الشراء بمبلغ {trade_size_usdt}$...")
                
                # تنفيذ الشراء
                order = exchange.create_market_buy_order(symbol, trade_size_usdt / current_price)
                bought_amount = float(order['amount'])
                last_buy_price = float(order['average']) if 'average' in order else current_price
                print(f"✅ تم الشراء بنجاح! الكمية: {bought_amount:.2f} بسعر: {last_buy_price:.5f}")

            # حالة: البوت يملك عملات (ينتظر هدف الربح)
            else:
                # حساب سعر البيع المطلوب لتحقيق ربح 1 دولار
                # الصيغة: (سعر الشراء + (الربح المستهدف / الكمية))
                sell_price_target = last_buy_price + (target_profit / bought_amount)
                
                print(f"📈 الحالي
