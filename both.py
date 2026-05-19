import time
import os
import ccxt
import pandas as pd
import pandas_ta as ta

--- 1. إعدادات الاتصال بالمنصة (Bybit كمثال) ---
ملاحظة أمنية: يفضل دائماً وضع المفاتيح في متغيرات بيئة (Environment Variables)
exchange = ccxt.bybit({
'apiKey': os.getenv('BYBIT_API_KEY', 'YOUR_API_KEY_HERE'),
'secret': os.getenv('BYBIT_API_SECRET', 'YOUR_API_SECRET_HERE'),
'enableRateLimit': True,
'options': {
'defaultType': 'spot' # التداول الفوري (أكثر أماناً لمبلغ 100$)
}
})

--- 2. الإعدادات العامة للمضاربة ---
SYMBOL = 'KAS/USDT' # زوج التداول
TRADE_AMOUNT_USDT = 100 # حجم رأس المال
STOP_LOSS_PCT = 0.03 # وقف الخسارة 3%
TAKE_PROFIT_PCT = 0.06 # أخذ الربح 6%
TIMEFRAME = '15m' # إطار 15 دقيقة (مناسب للمضاربة اليومية السريعة)

def get_market_data(symbol, timeframe, limit=100):
"""جلب بيانات الشموع وحساب المؤشرات الفنية"""
try:
bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

# حساب المؤشرات الفنية باستخدام pandas_ta
df['ema_9'] = ta.ema(df['close'], length=9)
df['ema_21'] = ta.ema(df['close'], length=21)
df['rsi'] = ta.rsi(df['close'], length=14)

return df
except Exception as e:
print(f"خطأ في جلب البيانات: {e}")
return None

def check_signals(df):
"""تحليل الاستراتيجية الفنية واتخاذ القرار"""
if df is None or len(df) < 2:
return None

# جلب قيم الشمعة الحالية والشمعة السابقة للتأكد من التقاطع
current_row = df.iloc[-1]
previous_row = df.iloc[-2]

# شروط الشراء (Buy Signal):
# 1. تقاطع الـ EMA 9 فوق الـ EMA 21
# 2. مؤشر RSI أقل من 65 لضمان عدم الشراء عند قمة متضخمة
ema_cross_up = (previous_row['ema_9'] <= previous_row['ema_21']) and (current_row['ema_9'] > current_row['ema_21'])
rsi_safe = current_row['rsi'] < 65

if ema_cross_up and rsi_safe:
return 'BUY'

return None

def execute_trade():
"""الحلقة البرمجية التنفيذية للبوت"""
in_position = False
buy_price = 0.0

print(f"تم بدء بوت تداول {SYMBOL} بكفاءة عالية...")

while True:
try:
df = get_market_data(SYMBOL, TIMEFRAME)
if df is None:
time.sleep(30)
continue

current_price = df.iloc[-1]['close']

# حالة 1: البحث عن فرصة دخول (شراء)
if not in_position:
signal = check_signals(df)
if signal == 'BUY':
print(f"🚀 إشارة شراء مكتشفة عند سعر: {current_price}")

# حساب الكمية بناءً على 100 دولار وسعر السوق الحالي
quantity = TRADE_AMOUNT_USDT / current_price

# تنفيذ أمر شراء بسعر السوق (Market Order)
# order = exchange.create_market_buy_order(SYMBOL, quantity)

buy_price = current_price
in_position = True
print(f"✅ تم الشراء بنجاح. كمية: {quantity} KAS. السعر: {buy_price}")

# حالة 2: إدارة الصفقة المفتوحة (الخروج)
else:
# حساب مستويات الخروج
stop_loss_price = buy_price * (1 - STOP_LOSS_PCT)
take_profit_price = buy_price * (1 + TAKE_PROFIT_PCT)

print(f"📊 نراقب الصفقة | السعر الحالي: {current_price} | الهدف: {take_profit_price:.4f} | الوقف: {stop_loss_price:.4f}", end='\r')

# تحقق من ضرب وقف الخسارة أو أخذ الربح
if current_price <= stop_loss_price:
print(f"\n🛑 تم ضرب وقف الخسارة عند سعر: {current_price} (خسارة 3%)")
# exchange.create_market_sell_order(SYMBOL, quantity)
in_position = False

elif current_price >= take_profit_price:
print(f"\n💰 تم تحقيق الهدف وأخذ الربح عند سعر: {current_price} (ربح 6%)")
# exchange.create_market_sell_order(SYMBOL, quantity)
in_position = False

# فحص السوق كل دقيقة للتأكد من تحديث الأسعار دون استهلاك الـ API
time.sleep(60)

except Exception as e:
print(f"\n❌ حدث خطأ غير متوقع في نظام التداول: {e}")
time.sleep(60)

if name == "main":
# لتشغيل البوت، تأكد من تثبيت المكتبات عبر الأمر: pip install ccxt pandas pandas_ta
execute_trade()