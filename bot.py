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
    
    TRADE_PERCENTAGE = 0.50       
    TARGET_PROFIT_USDT = 2.0      
    MIN_PRICE = 0.0300
    MAX_PRICE = 0.0633

    print(f"🚀 BOT KAS STARTED | INTERVAL: 1 HOUR")

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
                            actual_usdt = safe_float(coin_data.get('availableToWithdraw')) or safe_float(coin_data.get('walletBalance'))
                        elif coin_data.get('coin') == coin:
                            actual_kas_in_wallet = safe_float(coin_data.get('walletBalance'))

            ticker = exchange.fetch_ticker(symbol)
            price = safe_float(ticker.get('last')) if ticker else 0.0
            if price == 0.0:
                time.sleep(60)
                continue

            current_kas_value = actual_kas_in_wallet * price
            dynamic_trade_size = min(actual_usdt * TRADE_PERCENTAGE, 30.0)

            last_buy_price = price
            try:
                trades = exchange.fetch_my_trades(symbol, limit=5)
                if trades:
                    for t in reversed(trades):
                        if t.get('side') == 'buy':
                            last_buy_price = safe_float(t.get('price'))
                            break
            except Exception: pass

            if current_kas_value < 5.0:
                if actual_usdt >= dynamic_trade_size and dynamic_trade_size > 5.0:
                    if MIN_PRICE <= price <= MAX_PRICE:
                        quantity = dynamic_trade_size / price
                        print(f"🛒 BUYING KAS: {dynamic_trade_size:.2f}$")
                        exchange.create_market_buy_order(symbol, quantity)
            else:
                sell_price_target = last_buy_price + (TARGET_PROFIT_USDT / actual_kas_in_wallet)
                print(f"⚙️ KAS MONITORING | TARGET: {sell_price_target:.5f} | CURRENT: {price:.5f}")
                if price >= sell_price_target:
                    print("💰 TARGET REACHED! SELLING...")
                    exchange.create_market_sell_order(symbol, actual_kas_in_wallet)

        except Exception as e:
            print(f"❌ ERROR: {e}")
            
        time.sleep(3600) # فحص كل ساعة

if __name__ == "__main__":
    run_trading_bot()
