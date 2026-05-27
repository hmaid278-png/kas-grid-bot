import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

# إعداد المنصة للوصول المباشر للحساب الموحد V5
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'unified'
    }
})

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
    
    # --- إعدادات رأس المال بعد قراءة الدورة السعرية الحالية ---
    BOT_OPERATIONAL_CASH = 160.0  # حجم الكاش الذي يُسمح للبوت بتدويره والتحكم به
    TRADE_PERCENTAGE = 0.25       # حجم الصفقة (25% من الكاش المتاح للعمل المستقل = 40$)
    TARGET_PROFIT_USDT = 2.0      # الربح المستهدف الصافي بالدولار للera الجديدة
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    
    print(f"🚀 تم تشغيل البوت بحماية المحفظة التاريخية ونظام الـ 6 ساعات الصارم..")

    while True:
        try:
            unified_balance = exchange.privateGetV5AccountWalletBalance({
                'accountType': 'UNIFIED'
            })
            
            actual_usdt = 0.0
            actual_kas_in_wallet = 0.0
            
            if 'result' in unified_balance and 'list' in unified_balance['result']:
                account_list = unified_balance['result']['list']
                if account_list:
                    if 'coin' in account_list[0]:
                        for coin_data in account_list[0]['coin']:
                            if coin_data.get('coin') == 'USDT':
                                actual_usdt = safe_float(coin_data.get('availableToWithdraw'))
                                if actual_usdt == 0.0:
                                    actual_usdt = safe_float(coin_data.get('walletBalance'))
                            elif coin_data.get('coin') == coin:
                                actual_kas_in_wallet = safe_float(coin_data.get('walletBalance'))

            # حساب القيمة الإجمالية لكاسبا في المحفظة
            ticker = exchange.fetch_ticker(symbol)
            price = safe_float(ticker.get('last')) if ticker else 0.0
            if price == 0.0:
                time.sleep(60)
                continue

            current_kas_value = actual_kas_in_wallet * price
            
            # 🛡️ التعديل الجوهري لحماية المخزون القديم:
            # البوت يحسب فقط الكمية الجديدة التي يشتريها بـ الكاش الحالي، ويتجاهل المخزون التاريخي عند الفحص
            print(f"📊 فحص -> الكاش الحر: {actual_usdt:.2f}$ | إجمالي قيمة كاسبا بالمحفظة: {current_kas_value:.2f}$")

            # حساب حجم الصفقة بناءً على الكاش التشغيلي المتاح
            dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
            if dynamic_trade_size > 40.0:
                dynamic_trade_size = 40.0

            # جلب آخر صفقة تمت لمعرفة هل هناك صفقة تداول آلي مفتوحة أم لا
            last_trade_side = 'sell'
            last_buy_price = price
            try:
                trades = exchange.fetch_my_trades(symbol, limit=5)
                if trades:
                    for t in reversed(trades):
                        if t.get('side') is not None:
                            last_trade_side = t.get('side')
                            last_buy_price = safe_float(t.get('price'))
                            break
            except Exception:
                pass

            # حالة 1: الشراء (إذا كانت آخر حركة هي بيع، والكاش متاح)
            if last_trade_side == 'sell':
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🛒 إرسال أمر شراء ماركت جديد بقيمة: {dynamic_trade_size:.2f}$ عند السعر: {price:.5f}")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                        print("✅ تم الشراء بنجاح وجاري بدء المراقبة الدورية للهدف.")
                    else:
                        print(f"⚠️ السعر الحالي {price:.5f} خارج النطاق المسموح لبوت الشراء.")
                else:
                    print("🎰 السيولة المتاحة في الكاش غير كافية حالياً لفتح صفقة جديدة.")
            
            # حالة 2: مراقبة صفقة البوت الحالية المستقلة للبيع بربح 2$
            else:
                # نحدد كمية البيع بناءً على حجم الصفقة الأخيرة فقط لحماية بقية مخزون المحفظة القديم
                trade_qty = dynamic_trade_size / last_buy_price if last_buy_price > 0 else 0
                if trade_qty > 0 and actual_kas_in_wallet >= trade_qty:
                    sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / trade_qty)
                    stop_loss_price = last_buy_price * 0.95
                    
                    print(f"⚙️ يراقب صفقة البوت المستقلة | سعر الدخول: {last_buy_price:.5f} | هدف البيع الحالي: {sell_price_target:.5f}")
                    
                    if price >= sell_price_target:
                        print("💰 وصل السعر لهدف البوت! بيع كمية الصفقة الحالية فقط...")
                        exchange.create_market_sell_order(symbol, trade_qty)
                        print("✅ تم جني الأرباح المحدودة بنجاح وضمها للكاش.")
                    elif price <= stop_loss_price:
                        print("⚠️ تفعيل وقف الخسارة لحجم صفقة البوت...")
                        exchange.create_market_sell_order(symbol, trade_qty)

        except Exception as e:
            print(f"❌ خطأ في التنفيذ أو قراءة البيانات: {e}")
            
        print("-------------------------------------------------------------------------")
        # --- التعديل المعتمد: الانتظار 6 ساعات كاملة بين الفترات (21600 ثانية) ---
        time.sleep(21600) 

if __name__ == "__main__":
    run_trading_bot()
