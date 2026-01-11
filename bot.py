import os
import json
import requests
import yfinance as yf
from datetime import datetime

# ====== ENV จาก GitHub Secrets ======
BOT_TOKEN = os.environ["8444957235:AAF9FDV3cx_p5H1RRrOXNI7xwwdSMjZoOJg"]
CHAT_ID = os.environ["6744596307"]

STATE_FILE = "state.json"

# ====== โหลด / เซฟ สถานะ (กันแจ้งซ้ำ) ======
def load_state():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# ====== เช็กสินทรัพย์ ======
def check_asset(symbol, name, th1, th2):
    data = yf.download(
        symbol,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return f"⚠️ {name}: ดึงข้อมูลไม่ได้", "error"

    current = data["Close"].iloc[-1].item()
    high_1y = data["Close"].max().item()
    drop_pct = (current - high_1y) / high_1y * 100

    if drop_pct <= -th2:
        return f"🚨 {name}: ย่อลึก {drop_pct:.2f}% → ลงเพิ่มได้", "level2"
    elif drop_pct <= -th1:
        return f"⚠️ {name}: ย่อ {drop_pct:.2f}% → ลงได้ 1 ก้อน", "level1"
    elif drop_pct > 0:
        return f"📈 {name}: ทำจุดสูงสุดใหม่ → ไม่ควรไล่ราคา", "up"
    else:
        return f"⏳ {name}: ยังไม่เข้าเงื่อนไข ({drop_pct:.2f}%) → ไม่ควรลง", "wait"

# ====== โหลดสถานะเดิม ======
state = load_state()

# ====== เช็กตลาด ======
sp_msg, sp_level = check_asset("SPY", "S&P 500 (ตลาดกว้าง)", 10, 15)
qqq_msg, qqq_level = check_asset("QQQ", "Nasdaq / AI", 10, 15)
gld_msg, gld_level = check_asset("GLD", "ทองคำโลก", 5, 8)

summary = {
    "SPY": sp_level,
    "QQQ": qqq_level,
    "GLD": gld_level
}

today = datetime.now().strftime("%d/%m/%Y")

# ====== แจ้งเฉพาะเมื่อสถานะเปลี่ยน ======
if summary != state:
    message = (
        f"☀️ รายงานตลาดเช้า {today}\n\n"
        f"{sp_msg}\n"
        f"{qqq_msg}\n"
        f"{gld_msg}"
    )

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(
        url,
        data={"chat_id": CHAT_ID, "text": message}
    )

    save_state(summary)
else:
    print("สถานะเดิม — ไม่แจ้งซ้ำ")
