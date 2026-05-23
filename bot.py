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
    trade_size_usdt = 36.0
    target_profit = 2.0
    min_price = 0.0300
    max_price = 0.0633
    
    print(f"🚀 بوت 180$ (نسخة الذاكرة الذكية) يعمل الآن...")

    while True:
        try:
            # 1. قراءة محفظتك مباشرة لمعرفة هل تملك عملات أم لا
            balance = exchange.fetch_balance()
            kas_balance = float(balance['total'].get(coin, 0))
            
            ticker = exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                time.sleep(60)
                continue
            price = float(ticker['last'])

            # حالة 1: المحفظة فارغة من KAS (أقل من 10 حبات يعتبر فكة) -> جاهز للشراء
            if kas_balance < 10:  
                if min_price <= price <= max_price:
                    print(f"🔎 المحفظة جاهزة للشراء. السعر {price:.5f} | شراء بـ {trade_size_usdt}$...")
                    exchange.create_market_buy_order(symbol, trade_size_usdt / price)
                    print("✅ تم الشراء بنجاح!")
                else:
                    print(f"⚠️ السعر {price:.5f} خارج النطاق. انتظار...")
            
            # حالة 2: المحفظة بها KAS مسبقاً -> جاهز للبيع والمراقبة
            else:
                # جلب آخر سعر شراء من سجل المنصة مباشرة لمعرفة نقطة الصفر
                trades = exchange.fetch_my_trades(symbol, limit=10)
                last_buy_price = price # قيمة افتراضية
                for t in reversed(trades):
                    if t['side'] == 'buy':
                        last_buy_price = float(t['price'])
                        break

                sell_price_target = last_buy_price + (target_profit / kas_balance)
                stop_loss_price = last_buy_price * 0.95
                
                print(f"📈 نملك {kas_balance:.2f} KAS | السعر الحالي: {price:.5f} | هدف البيع: {sell_price_target:.5f}")
                
                if price >= sell_price_target:
                    exchange.create_market_sell_order(symbol, kas_balance)
                    print(f"💰 تم جني الربح بنجاح!")
                elif price <= stop_loss_price:
                    exchange.create_market_sell_order(symbol, kas_balance)
                    print(f"⚠️ انخفاض حاد! تفعيل وقف الخسارة.")

        except Exception as e:
            print(f"❌ خطأ تقني: {e}")
            
        time.sleep(10800) # فحص كل 3 ساعات (10800 ثانية)

if __name__ == "__main__":
    run_trading_bot()

