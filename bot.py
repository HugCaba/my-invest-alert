import os
import requests
import yfinance as yf
from datetime import datetime

# ====== ENV จาก GitHub Secrets ======
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ====== เช็กสินทรัพย์ ======
def check_asset(symbol, name, th1, th2):
    data = yf.download(
        symbol,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return f"⚠️ {name}: ดึงข้อมูลไม่ได้"

    current = data["Close"].iloc[-1].item()
    high_1y = data["Close"].max().item()
    drop_pct = (current - high_1y) / high_1y * 100

    if drop_pct <= -th2:
        return f"🚨 {name}: ย่อลึก {drop_pct:.2f}% → ลงเพิ่มได้"
    elif drop_pct <= -th1:
        return f"⚠️ {name}: ย่อ {drop_pct:.2f}% → ลงได้ 1 ก้อน"
    elif drop_pct > 0:
        return f"📈 {name}: ทำจุดสูงสุดใหม่ → ไม่ควรไล่ราคา"
    else:
        return f"⏳ {name}: ยังไม่เข้าเงื่อนไข ({drop_pct:.2f}%)"

# ====== เช็กตลาด ======
sp_msg = check_asset("SPY", "S&P 500 (ตลาดกว้าง)", 10, 15)
qqq_msg = check_asset("QQQ", "Nasdaq / AI", 10, 15)
gld_msg = check_asset("GLD", "ทองคำโลก", 5, 8)

now = datetime.now().strftime("%d/%m/%Y %H:%M")

message = (
    f"📊 รายงานตลาด ({now})\n\n"
    f"{sp_msg}\n"
    f"{qqq_msg}\n"
    f"{gld_msg}"
)

# ====== ส่ง Telegram ======
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)
