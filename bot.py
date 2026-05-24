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
    
    # --- قيد الميزانية الصارم ---
    MAX_TRADING_BUDGET = 180.0  # الميزانية الإجمالية المسموح للبوت برؤيتها
    TRADE_SIZE_USDT = 40.0      # حجم الصفقة الواحدة الثابت
    TARGET_PROFIT_USDT = 2.0    # الربح المستهدف الصافي بالدولار عند البيع
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل البوت الصارم.. الميزانية المتاحة للتداول: {MAX_TRADING_BUDGET}$ فقط.")
    print(f"🔒 تم حظر وعزل باقي أصول المحفظة تلقائياً عن أمر البوت.")

    while True:
        try:
            # جلب الرصيد الفعلي من المنصة
            balance = exchange.fetch_balance()
            actual_usdt = float(balance['free'].get('USDT', 0))
            
            # حساب الرصيد الذي يسمح البوت لنفسه برؤيته فقط (خصم أموال الأمان)
            # إذا كان الرصيد الكلي 563$، البوت سيتعامل فقط مع ما لا يتعدى الـ 180$
            trading_allowed_usdt = actual_usdt - 400.0
            if trading_allowed_usdt > MAX_TRADING_BUDGET:
                trading_allowed_usdt = MAX_TRADING_BUDGET
            elif trading_allowed_usdt < 0:
                trading_allowed_usdt = 0.0

            ticker = exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                time.sleep(60)
                continue
            price = float(ticker['last'])

            print(f" Total USDT in Account: {actual_usdt:.2f}$ | Budget Allowed for Bot: {trading_allowed_usdt:.2f}$")

            # جلب آخر عملية شراء قام بها البوت لمعرفة السعر والكمية الدقيقة
            trades = exchange.fetch_my_trades(symbol, limit=5)
            last_buy_price = None
            bot_purchased_qty = None

            for t in reversed(trades):
                if t['side'] == 'buy':
                    last_buy_price = float(t['price'])
                    bot_purchased_qty = float(t['amount']) # الكمية الفعليه التي اشتراها البوت بـ 40$
                    break

            # حالة 1: البوت لم يشترِ بعد، أو قام بالبيع مؤخراً (لا توجد صفقات معلقة للبوت)
            # نتحقق من ذلك إذا كانت آخر عملية في السجل هي "sell" أو لا يوجد كمية مسجلة
            last_trade_side = trades[-1]['side'] if trades else 'sell'
            
            if last_trade_side == 'sell' or bot_purchased_qty is None:
                # التأكد من توفر سيولة كافية للشراء داخل حدود الـ 180$ المسموحة
                if trading_allowed_usdt >= TRADE_SIZE_USDT:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = TRADE_SIZE_USDT / price
                        print(f"🔎 النظام جاهز. السعر الحالي: {price:.5f} | تنفيذ شراء بـ {TRADE_SIZE_USDT}$ فقط...")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء المحدود بنجاح!")
                    else:
                        print(f"⚠️ السعر {price:.5f} خارج النطاق المسموح. انتظار...")
                else:
                    print("🎰 لا توجد سيولة كافية مخصصة للتداول حالياً (أموال الأمان محمية).")
            
            # حالة 2: البوت لديه صفقة شراء مفتوحة بـ 40$ ويقوم بمراقبتها لحجمها فقط
            else:
                # حساب أهداف البيع والوقف بناءً على السعر الفعلي للشراء والكمية الدقيقة التي دخل بها البوت
                sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / bot_purchased_qty)
                stop_loss_price = last_buy_price * 0.95
                
                print(f"⚙️ يراقب صفقة الشراء الحالية: السعر المشتري به {last_buy_price:.5f} | الكمية المحمية: {bot_purchased_qty:.2f} KAS")
                print(f"📊 السعر الحالي: {price:.5f} | هدف البيع: {sell_price_target:.5f} | وقف الخسارة: {stop_loss_price:.5f}")
                
                # أخذ القرار للكمية المشتراة من قبل البوت فقط دون لمس بقية أصول المحفظة
                if price >= sell_price_target:
                    print("💰 السعر ضرب الهدف المستهدف! بيع كمية الصفقة المحددة فقط...")
                    exchange.create_market_sell_order(symbol, bot_purchased_qty)
                    print("✅ تم جني الربح بنجاح ودون مساس بالمدخرات!")
                elif price <= stop_loss_price:
                    print("⚠️ تفعيل وقف الخسارة لصفقة الـ 40$ لحماية رأس المال...")
                    exchange.create_market_sell_order(symbol, bot_purchased_qty)
                    print("⚠️ تم الخروج من الصفقة بنجاح.")

        except Exception as e:
            print(f"❌ خطأ في التنفيذ أو قراءة البيانات: {e}")
            
        print("-------------------------------------------------------------------------")
        time.sleep(10800) # فحص دوري صارم كل 3 ساعات دائم ودون توقف

if __name__ == "__main__":
    run_trading_bot()
