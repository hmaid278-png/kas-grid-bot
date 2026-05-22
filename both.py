
def place_buy(price):
    try:
        qty = round(ORDER_SIZE / price, 2)
        if qty <= 0:
            return None
        session.place_order(
            category="spot",
            symbol=SYMBOL,
            side="Buy",
            orderType="Limit",
            qty=str(qty),
            price=str(price),
            timeInForce="GTC",
        )
        log.info(f"🟢 BUY  | {qty} KAS @ ${price:.3f}")
        return True
    except Exception as e:
        log.error(f"❌ Buy failed: {e}")
        return None

def place_sell(price, qty):
    try:
        qty = round(qty * 0.99, 2)
        if qty <= 0:
            return None
        session.place_order(
            category="spot",
            symbol=SYMBOL,
            side="Sell",
            orderType="Limit",
            qty=str(qty),
            price=str(price),
            timeInForce="GTC",
        )
        log.info(f"🔴 SELL | {qty} KAS @ ${price:.3f}")
        return True
    except Exception as e:
        log.error(f"❌ Sell failed: {e}")
        return None

# Main loop
cycle = 0
while True:
