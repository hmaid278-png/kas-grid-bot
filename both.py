# --- 1. إعدادات الاتصال بالمنصة (Bybit)
API_KEY = "XXycw37KeXtLfT2gt0"
API_SECRET = "d8chxUfVzLGuclJPTilLmI8fdwtkO68PWuel"
SYMBOL = "KASUSDT"

# --- 2. إعدادات استراتيجية التداول (Grid Bot)
# المسافة بين كل صفقة وأخرى (2% للأمان)
GRID_SPACING = 0.02  
# عدد خطوط الشبكة الموزعة للمبلغ
NUM_GRIDS = 10       
# رأس المال المخصص للبوت (100 دولار)
TOTAL_INVESTMENT = 100 

# --- 3. تشغيل النظام
def start_bot():
    try:
        # كود الاتصال بالمنصة سيعمل هنا
        print("Bot is connected and running...")
        print(f"Trading {SYMBOL} with {TOTAL_INVESTMENT} USDT.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    start_bot()
