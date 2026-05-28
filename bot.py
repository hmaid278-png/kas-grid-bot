import ccxt
import os
import time

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'unified'}
})

def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def run_trading_bot():
    symbol = 'KAS/USDT'
    coin = 'KAS'
    
    KAS_OPERATIONAL_CASH = 60.0   
    TRADE_PERCENTAGE = 0.50       
    TARGET_PROFIT_USDT = 2.0      
    
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633
    historical_buy_price = 0.032  

    print(f"🚀 تم تشغيل بوت KAS (نظام التسييل الآمن - بدون وقف خسارة) وفحص كل 6 ساعات...")

    while True:
        try:
            unified_balance = exchange.privateGetV5AccountWalletBalance({'accountType': 'UNIFIED'})
            
            actual_usdt = 0.0
            actual_kas_in_wallet = 0.0
            
            if 'result' in unified_balance and 'list' in unified_balance['result']:
                account_list = unified_balance['result']['list']
                if account_list and 'coin' in account_list[0]:
                    for coin_data in account_list[0]['coin']:
                        if coin_data.get('coin') == 'USDT':
                            actual_usdt = safe_float(coin_data.get('availableToWithdraw'))
                            if actual_usdt == 0.0:
                                actual_usdt = safe_float(coin_data.get('walletBalance'))
                        elif coin_data.get('coin') == coin:
                            actual_kas_in_wallet = safe_float(coin_data.get('walletBalance'))

            ticker = exchange.fetch_ticker(symbol)
            price = safe_float(ticker.get('last')) if ticker else 0.0
            if price == 0.0:
                time.sleep(60)
                continue

            current_kas_value = actual_kas_in_wallet * price
            dynamic_trade_size = actual_usdt * TRADE_PERCENTAGE
            if dynamic_trade_size > 30.0: dynamic_trade_size = 30.0

            # تحديد حالة الحساب
            if current_kas_value >= 5.0:
                last_trade_side = 'buy'
                if actual_kas_in_wallet > 1000:
                    last_buy_price = historical_buy_price
                else:
                    last_buy_price = price
            else:
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
                except Exception: pass

            print(f"📊 [بوت KAS] الكاش الحر: {actual_usdt:.2f}$ | قيمة كاسبا في المحفظة: {current_kas_value:.2f}$")

            # حالة الشراء (تُفعل فقط إذا كانت المحفظة خالية تماماً)
            if last_trade_side == 'sell' and current_kas_value < 5.0:
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity_to_buy = dynamic_trade_size / price
                        print(f"🛒 شراء صفقة مستقلة جديدة بقيمة: {dynamic_trade_size:.2f}$ عند سعر: {price:.5f}")
                        exchange.create_market_buy_order(symbol, quantity_to_buy)
                    else:
                        print(f"⚠️ سعر كاسبا الحالي خارج نطاق الشراء المسموح.")
                else:
                    print("🎰 الكاش المتبقي غير كافي حالياً لفتح صفقة.")
            
            # حالة مراقبة الهدف للبيع بربح فقط (تم حذف وقف الخسارة تماماً لحمايتك)
            elif current_kas_value >= 5.0:
                if actual_kas_in_wallet > 0:
                    sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / actual_kas_in_wallet)
                    print(f"⚙️ يراقب المحفظة للتسييل | سعر الدخول: {last_buy_price:.5f} | هدف البيع المطلوب بربح (+2$): {sell_price_target:.5f} | السعر الآن: {price:.5f}")
                    
                    if price >= sell_price_target:
                        print("💰 صعد السعر للهدف! تسييل كامل المحفظة فوراً ماركت وجني الأرباح الكاش...")
                        exchange.create_market_sell_order(symbol, actual_kas_in_wallet)

        except Exception as e:
            print(f"❌ خطأ في تنفيذ بوت KAS: {e}")
            
        print("-------------------------------------------------------------------------")
        time.sleep(21600) # فحص كل 6 ساعات تماماً

if __name__ == "__main__":
    run_trading_bot()
