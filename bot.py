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

# 🛡️ دالة أمان صارمة لتحويل أي قيمة إلى رقم وتجنب خطأ NoneType نهائياً
def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def run_trading_bot():
    symbol = 'KAS/USDT'
    coin = 'KAS'
    
    # --- إعدادات إعادة استثمار الأرباح والتكبير التلقائي ---
    MAX_ALLOWED_BALANCE = 200.0   # سقف الأمان للحساب (200$ فما دون)
    TRADE_PERCENTAGE = 0.20       # حجم الصفقة = 20% من الرصيد المتاح (تكبر مع الأرباح)
    TARGET_PROFIT_USDT = 2.0      # الربح المستهدف الصافي بالدولار
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل البوت مع درع الحماية ضد أخطاء (NoneType)..")

    while True:
        try:
            # جلب الرصيد الفعلي من المنصة بأمان
            balance = exchange.fetch_balance()
            
            raw_usdt = balance.get('USDT', {})
            actual_usdt = safe_float(raw_usdt.get('free', raw_usdt.get('total', 0.0)))
            
            raw_kas = balance.get(coin, {})
            actual_kas_in_wallet = safe_float(raw_kas.get('free', raw_kas.get('total', 0.0)))

            print(f"📊 الرصيد المتاح: {actual_usdt:.2f}$ | رصيد كاسبا: {actual_kas_in_wallet:.2f} KAS")

            # الحماية الصارمة
            if actual_usdt > MAX_ALLOWED_BALANCE:
                print(f"🛑 حظر تلقائي: الرصيد المتاح ({actual_usdt:.2f}$) أكبر من 200$. تم إيقاف العمل لحماية المحفظة.")
                print("-------------------------------------------------------------------------")
                time.sleep(10800)
                continue

            ticker = exchange.fetch_ticker(symbol)
            if not ticker or ticker.get('last') is None:
                time.sleep(60)
                continue
                
            price = safe_float(ticker.get('last'))
            if price == 0.0:
                time.sleep(60)
                continue

            # حساب حجم الصفقة الديناميكي
            dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
            if dynamic_trade_size > 40.0 and actual_usdt <= 200.0:
                pass 
            elif dynamic_trade_size > 40.0:
                dynamic_trade_size = 40.0

            # جلب آخر سعر شراء بأمان تام
            trades = exchange.fetch_my_trades(symbol, limit=5)
            last_buy_price = price 
            
            if trades:
                for t in reversed(trades):
                    if t.get('side') == 'buy' and t.get('price') is not None:
                        last_buy_price = safe_float(t.get('price'))
                        break

            # حالة 1: الشراء
            if (actual_kas_in_wallet * price) < 5.0:
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🔎 الرصيد مطابق للشروط. حجم الصفقة (تكبير تلقائي): {dynamic_trade_size:.2f}$")
                        print(f"🛒 تنفيذ أمر شراء عند السعر الحالي: {price:.5f}...")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء التراكمي بنجاح!")
                    else:
                        print(f"⚠️ السعر {price:.5f} خارج النطاق السعري المسموح.")
                else:
                    print("🎰 الرصيد المتاح غير كافٍ لفتح صفقة جديدة.")
            
            # حالة 2: المراقبة والبيع
            else:
                current_qty = actual_kas_in_wallet
                if current_qty > 0:
                    sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / current_qty)
                    stop_loss_price = last_buy_price * 0.95
                    
                    print(f"⚙️ يراقب صفقة مستثمرة | كمية المحفظة الحالية: {current_qty:.2f} KAS")
                    print(f"📊 السعر الحالي: {price:.5f} | هدف البيع: {sell_price_target:.5f} | وقف الخسارة: {stop_loss_price:.5f}")
                    
                    if price >= sell_price_target:
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("✅ تم جني الربح وإعادة إدخاله في سيولة الحساب للتكبير القادم!")
                    elif price <= stop_loss_price:
                        exchange.create_market_sell_order(symbol, current_qty)
                        print("⚠️ تم الخروج من الصفقة لحماية المحفظة.")

        except Exception as e:
            print(f"❌ خطأ في التنفيذ أو قراءة البيانات: {e}")
            
        print("-------------------------------------------------------------------------")
        time.sleep(10800) # فحص دوري مستمر دائم ودون توقف كل 3 ساعات

if __name__ == "__main__":
    run_trading_bot()
