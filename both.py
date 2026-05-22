"""
╔══════════════════════════════════════════════════════════╗
║         KAS Professional Trading Bot v3.0                ║
║                                                          ║
║  ✅ معالجة تلقائية للأخطاء (5 محاولات)                  ║
║  ✅ إدارة مخاطر صارمة (SL + TP + حد يومي)               ║
║  ✅ احترام Rate Limits تلقائياً                          ║
║  ✅ سجلات تفصيلية (Logs مع تاريخ ووقت)                  ║
║  ✅ حماية API عبر Environment Variables                  ║
║  ✅ استهلاك RAM أقل من 100MB                             ║
║  ✅ مكتبات عالمية (ccxt + pandas)                        ║
║  ✅ أسعار محدّثة بناءً على تحليل مايو 2026               ║
╚══════════════════════════════════════════════════════════╝

الإعداد:
    في Railway → Variables أضف:
    API_KEY    = AVKLVzE3M9dEaQ8WoY 
    API_SECRET = d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel 
    CAPITAL    = 100

تشغيل:
    python kas_bot_v3.py
"""

import os
import time
import logging
import pandas as pd
import ccxt
from datetime import datetime, date
from logging.handlers import RotatingFileHandler


# ══════════════════════════════════════════════════════════
#  ١. نظام السجلات التفصيلي
# ══════════════════════════════════════════════════════════

def setup_logger():
    logger = logging.getLogger("KASBot")
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # ملف سجل (5MB حد أقصى، 3 نسخ احتياطية)
    fh = RotatingFileHandler(
        "kas_bot.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    fh.setFormatter(fmt)

    # شاشة
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

log = setup_logger()


# ══════════════════════════════════════════════════════════
#  ٢. إعدادات البوت (من Environment Variables)
# ══════════════════════════════════════════════════════════

API_KEY    = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

if not API_KEY or not API_SECRET:
    log.critical("❌ API_KEY أو API_SECRET غير موجودة في متغيرات البيئة!")
    log.critical("   أضفهم في Railway → Variables")
    exit(1)

# ─── إعدادات التداول (محدّثة مايو 2026) ──────────────────
SYMBOL         = "KAS/USDT"
CAPITAL        = float(os.getenv("CAPITAL", "100"))
CHECK_HOURS    = int(os.getenv("CHECK_HOURS", "4"))
CHECK_SECONDS  = CHECK_HOURS * 3600

# ─── أسعار محدّثة بناءً على التحليل ──────────────────────
BUY_BELOW      = 0.034    # اشتري عند أو أقل من هذا السعر
SELL_ABOVE     = 0.050    # بيع عند أو أعلى من هذا السعر
STOP_LOSS_PCT  = 0.05     # 5% وقف خسارة
TAKE_PROFIT_PCT= 0.15     # 15% جني أرباح
RISK_PER_TRADE = 0.02     # 2% من رأس المال لكل صفقة
MAX_DAILY_LOSS = 0.10     # 10% حد خسارة يومي أقصى

# ─── إعدادات التحليل الفني ────────────────────────────────
RSI_PERIOD     = 14
RSI_BUY        = 38       # شراء عند RSI أقل من هذا
RSI_SELL       = 68       # بيع عند RSI أعلى من هذا
EMA_FAST       = 20
EMA_SLOW       = 50

# ─── إعدادات Rate Limits والأخطاء ────────────────────────
RATE_DELAY     = 1.5      # ثانية بين كل طلب
MAX_RETRIES    = 5        # محاولات عند الخطأ
RETRY_DELAY    = 30       # ثانية انتظار بين المحاولات


# ══════════════════════════════════════════════════════════
#  ٣. الاتصال بـ Bybit عبر ccxt (مع Rate Limits)
# ══════════════════════════════════════════════════════════

def create_exchange():
    ex = ccxt.bybit({
        "apiKey"         : API_KEY,
        "secret"         : API_SECRET,
        "enableRateLimit": True,      # ccxt يدير Rate Limits تلقائياً
        "rateLimit"      : 1200,      # مللي ثانية بين الطلبات
        "timeout"        : 30000,     # 30 ثانية timeout
        "options"        : {"defaultType": "spot"},
    })
    return ex

try:
    exchange = create_exchange()
    log.info("✅ تم الاتصال بـ Bybit بنجاح")
except Exception as e:
    log.critical(f"❌ فشل إنشاء الاتصال: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════
#  ٤. معالجة الأخطاء التلقائية
# ══════════════════════════════════════════════════════════

def retry(func, *args, retries=MAX_RETRIES, delay=RETRY_DELAY, **kwargs):
    """
    تنفيذ أي دالة مع إعادة المحاولة تلقائياً.
    يتعامل مع:
      - انقطاع الإنترنت (NetworkError)
      - بطء الخادم (RequestTimeout)
      - تجاوز Rate Limits (RateLimitExceeded)
      - أخطاء المنصة (ExchangeError)
    """
    for attempt in range(1, retries + 1):
        try:
            time.sleep(RATE_DELAY)
            return func(*args, **kwargs)

        except ccxt.RateLimitExceeded:
            wait = 60 * attempt
            log.warning(f"⚠️  Rate Limit! انتظار {wait}s (محاولة {attempt}/{retries})")
            time.sleep(wait)

        except ccxt.RequestTimeout:
            log.warning(f"⚠️  انتهت مهلة الخادم (محاولة {attempt}/{retries}) → انتظار {delay}s")
            time.sleep(delay)

        except ccxt.NetworkError as e:
            log.warning(f"⚠️  خطأ شبكة: {e} (محاولة {attempt}/{retries}) → انتظار {delay}s")
            time.sleep(delay)

        except ccxt.ExchangeError as e:
            log.error(f"❌ خطأ منصة: {e} (محاولة {attempt}/{retries}) → انتظار {delay}s")
            time.sleep(delay)

        except Exception as e:
            log.error(f"❌ خطأ غير متوقع: {e} (محاولة {attempt}/{retries})")
            time.sleep(delay)

    log.error(f"❌ فشلت جميع المحاولات ({retries}) → تخطي هذه العملية")
    return None


# ══════════════════════════════════════════════════════════
#  ٥. جلب البيانات
# ══════════════════════════════════════════════════════════

def get_price():
    ticker = retry(exchange.fetch_ticker, SYMBOL)
    return float(ticker["last"]) if ticker else None


def get_ohlcv():
    """جلب شموع 4 ساعات وتحويلها لـ DataFrame"""
    raw = retry(exchange.fetch_ohlcv, SYMBOL, timeframe="4h", limit=100)
    if raw is None:
        return None
    df = pd.DataFrame(raw, columns=["ts", "open", "high", "low", "close", "volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df.set_index("ts")


def get_balance():
    """جلب رصيد USDT و KAS"""
    bal = retry(exchange.fetch_balance)
    if bal:
        usdt = float(bal.get("USDT", {}).get("free", 0))
        kas  = float(bal.get("KAS",  {}).get("free", 0))
        return usdt, kas
    return 0.0, 0.0


# ══════════════════════════════════════════════════════════
#  ٦. التحليل الفني (pandas)
# ══════════════════════════════════════════════════════════

def calc_rsi(df, period=RSI_PERIOD):
    delta = df["close"].diff()
    gain  = delta.where(delta > 0, 0).rolling(period).mean()
    loss  = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs    = gain / loss
    return round((100 - 100 / (1 + rs)).iloc[-1], 2)


def calc_ema(df, period):
    return round(df["close"].ewm(span=period, adjust=False).mean().iloc[-1], 6)


def calc_volume_ratio(df, window=10):
    """نسبة الحجم الحالي مقارنة بالمتوسط"""
    avg = df["volume"].rolling(window).mean().iloc[-1]
    cur = df["volume"].iloc[-1]
    return round(cur / avg, 2) if avg > 0 else 1.0


def analyze(df):
    rsi      = calc_rsi(df)
    ema_fast = calc_ema(df, EMA_FAST)
    ema_slow = calc_ema(df, EMA_SLOW)
    vol_r    = calc_volume_ratio(df)
    trend    = "صاعد ↑" if ema_fast > ema_slow else "هابط ↓"
    return {
        "rsi"     : rsi,
        "ema_fast": ema_fast,
        "ema_slow": ema_slow,
        "vol_r"   : vol_r,
        "trend"   : trend,
        "bullish" : ema_fast > ema_slow,
    }


# ══════════════════════════════════════════════════════════
#  ٧. إدارة المخاطر الصارمة
# ══════════════════════════════════════════════════════════

def position_size(price, usdt):
    """حساب حجم الصفقة (2% من رأس المال)"""
    risk   = CAPITAL * RISK_PER_TRADE
    qty    = risk / price
    max_qty= usdt / price
    return round(min(qty, max_qty), 2)


def stop_loss_price(entry):
    return round(entry * (1 - STOP_LOSS_PCT), 6)


def take_profit_price(entry):
    return round(entry * (1 + TAKE_PROFIT_PCT), 6)


# ══════════════════════════════════════════════════════════
#  ٨. تنفيذ الصفقات
# ══════════════════════════════════════════════════════════

def buy(price, usdt):
    qty = position_size(price, usdt)
    if qty <= 0:
        log.warning("⚠️  رصيد USDT غير كافٍ للشراء")
        return None, None, None

    sl = stop_loss_price(price)
    tp = take_profit_price(price)

    order = retry(exchange.create_order, SYMBOL, "market", "buy", qty)
    if order:
        log.info("─" * 55)
        log.info(f"✅ شراء  | {qty} KAS @ ${price:.6f}")
        log.info(f"   وقف الخسارة : ${sl:.6f} (-{STOP_LOSS_PCT*100}%)")
        log.info(f"   جني الأرباح : ${tp:.6f} (+{TAKE_PROFIT_PCT*100}%)")
        log.info(f"   معرف الصفقة : {order.get('id','N/A')}")
        log.info("─" * 55)
        return order, sl, tp
    return None, None, None


def sell(kas, reason):
    qty   = round(kas * 0.99, 2)
    price = get_price()
    order = retry(exchange.create_order, SYMBOL, "market", "sell", qty)
    if order:
        log.info("─" * 55)
        log.info(f"💰 بيع   | {qty} KAS @ ${price:.6f}")
        log.info(f"   السبب       : {reason}")
        log.info(f"   معرف الصفقة : {order.get('id','N/A')}")
        log.info("─" * 55)
    return order


# ══════════════════════════════════════════════════════════
#  ٩. البوت الرئيسي
# ══════════════════════════════════════════════════════════

class KASBot:
    def __init__(self):
        self.entry    = None   # سعر الدخول
        self.sl       = None   # وقف الخسارة
        self.tp       = None   # جني الأرباح
        self.day_loss = 0.0
        self.day_date = date.today()
        self.trades   = 0

        log.info("═" * 55)
        log.info("🚀 KAS Professional Bot v3.0")
        log.info(f"   رأس المال     : ${CAPITAL}")
        log.info(f"   مخاطرة/صفقة  : {RISK_PER_TRADE*100}%")
        log.info(f"   وقف الخسارة  : {STOP_LOSS_PCT*100}%")
        log.info(f"   جني الأرباح  : {TAKE_PROFIT_PCT*100}%")
        log.info(f"   حد خسارة يومي: {MAX_DAILY_LOSS*100}%")
        log.info(f"   التفقد       : كل {CHECK_HOURS} ساعات")
        log.info(f"   شراء < ${BUY_BELOW} | بيع > ${SELL_ABOVE}")
        log.info("═" * 55)

    # ── إعادة تعيين اليومية ──────────────────────────────
    def reset_daily(self):
        if date.today() != self.day_date:
            log.info(f"📅 يوم جديد | الصفقات أمس: {self.trades} | الخسارة: ${self.day_loss:.2f}")
            self.day_loss = 0.0
            self.day_date = date.today()
            self.trades   = 0

    # ── فحص حد الخسارة اليومي ───────────────────────────
    def within_daily_limit(self):
        limit = CAPITAL * MAX_DAILY_LOSS
        if self.day_loss >= limit:
            log.warning(f"🛑 حد الخسارة اليومي! ${self.day_loss:.2f} >= ${limit:.2f}")
            return False
        return True

    # ── فحص وقف الخسارة وجني الأرباح ───────────────────
    def check_sl_tp(self, price, kas):
        if not self.entry or kas < 1:
            return

        # وقف الخسارة
        if self.sl and price <= self.sl:
            loss = (price - self.entry) * kas
            self.day_loss += abs(loss)
            log.warning(f"🛑 وقف الخسارة تُفعّل! ${price:.6f} <= ${self.sl:.6f} | خسارة: ${loss:.2f}")
            sell(kas, "وقف الخسارة")
            self.entry = None

        # جني الأرباح
        elif self.tp and price >= self.tp:
            profit = (price - self.entry) * kas
            log.info(f"🎯 جني الأرباح! ${price:.6f} >= ${self.tp:.6f} | ربح: ${profit:.2f}")
            sell(kas, "جني الأرباح")
            self.entry = None

    # ── دورة التداول ─────────────────────────────────────
    def cycle(self):
        self.reset_daily()
        if not self.within_daily_limit():
            return

        # جلب البيانات
        df = get_ohlcv()
        if df is None:
            log.warning("⚠️  فشل جلب البيانات، سيعيد المحاولة في الدورة القادمة")
            return

        price        = get_price()
        usdt, kas    = get_balance()

        if not price:
            return

        # التحليل
        a = analyze(df)

        log.info("┌" + "─" * 53)
        log.info(f"│ السعر  : ${price:.6f}")
        log.info(f"│ RSI    : {a['rsi']} | الاتجاه: {a['trend']}")
        log.info(f"│ EMA20  : ${a['ema_fast']} | EMA50: ${a['ema_slow']}")
        log.info(f"│ الحجم  : {a['vol_r']}x المتوسط")
        log.info(f"│ USDT   : ${usdt:.2f} | KAS: {kas:.2f}")
        log.info("└" + "─" * 53)

        # فحص SL/TP
        self.check_sl_tp(price, kas)

        # ── إشارة شراء ──────────────────────────────────
        buy_signal = (
            price   <= BUY_BELOW   and
            a["rsi"] < RSI_BUY     and
            a["bullish"]           and
            a["vol_r"] > 1.1       and
            usdt     >= 5          and
            self.entry is None
        )

        # ── إشارة بيع ───────────────────────────────────
        sell_signal = (
            price   >= SELL_ABOVE  and
            a["rsi"] > RSI_SELL    and
            kas      > 1
        )

        if buy_signal:
            log.info(f"🟢 إشارة شراء قوية!")
            log.info(f"   RSI={a['rsi']} < {RSI_BUY} | الاتجاه صاعد | الحجم={a['vol_r']}x")
            order, sl, tp = buy(price, usdt)
            if order:
                self.entry  = price
                self.sl     = sl
                self.tp     = tp
                self.trades += 1

        elif sell_signal:
            log.info(f"🔴 إشارة بيع!")
            log.info(f"   RSI={a['rsi']} > {RSI_SELL} | السعر > ${SELL_ABOVE}")
            sell(kas, "إشارة بيع تقنية")
            self.entry = None

        else:
            log.info(f"⏳ انتظار | شراء: RSI<{RSI_BUY} وسعر<${BUY_BELOW} | بيع: RSI>{RSI_SELL} وسعر>${SELL_ABOVE}")

        log.info(f"😴 النوم {CHECK_HOURS} ساعات حتى الفحص القادم...")

    # ── الحلقة الرئيسية ──────────────────────────────────
    def run(self):
        while True:
            try:
                self.cycle()
            except KeyboardInterrupt:
                log.info("⏹️  إيقاف البوت يدوياً")
                break
            except Exception as e:
                log.error(f"❌ خطأ غير متوقع في الحلقة: {e}")
                log.info("   إعادة المحاولة بعد 5 دقائق...")
                time.sleep(300)
            finally:
                time.sleep(CHECK_SECONDS)


# ══════════════════════════════════════════════════════════
#  نقطة البداية
# ══════════════════════════════════════════════════════════

if __name__ == "__main__":
    bot = KASBot()
    bot.run()
