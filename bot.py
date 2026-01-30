import os
import requests
import yfinance as yf
from datetime import datetime

# =========================
# ENV จาก GitHub Secrets
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# สินทรัพย์ที่ติดตาม
# =========================
assets = [
    ("GLD", "SPDR Gold Trust", "GLD"),
    ("BTC-USD", "Bitcoin", "BTC/USD"),
    ("SPY", "S&P 500", "US500"),
    ("GC=F", "ทองคำ (Gold Futures)", "GC"),
]

# =========================
# ฟังก์ชันสถานะ
# =========================
def get_status(pct):
    if pct > 1:
        return "🟢 ปกติ"
    elif pct < -1:
        return "🔴 อ่อนแรง"
    else:
        return "🟡 แกว่งตัว"

# =========================
# ฟังก์ชันคำแนะนำ
# =========================
def get_advice(drawdown):
    if drawdown > -5:
        return "ยังไม่ต้องรีบ รอจังหวะ", "0%"
    elif drawdown > -10:
        return "เริ่มสะสมเบา", "5%"
    elif drawdown > -20:
        return "ลงได้ 1 ก้อน", "10%"
    else:
        return "ลงหนัก (โอกาสดี)", "20%"

# =========================
# ดึงข้อมูลตลาด
# =========================
def get_data(symbol):
    data = yf.download(symbol, period="1y", interval="1h", progress=False)
    if len(data) < 2:
        return None

    now_price = data["Close"].iloc[-1].item()
    high_1y = data["Close"].max().item()
    drawdown = (now_price - high_1y) / high_1y * 100

    yesterday = yf.download(symbol, period="2d", interval="1h", progress=False)
    yesterday_close = yesterday["Close"].iloc[0].item()

    today_data = yesterday[yesterday.index.date == yesterday.index[-1].date()]
    today_open = today_data["Open"].iloc[0].item()

    pct_y = (now_price - yesterday_close) / yesterday_close * 100
    pct_t = (now_price - today_open) / today_open * 100

    return now_price, pct_y, pct_t, drawdown

# =========================
# สร้างข้อความ
# =========================
now = datetime.now().strftime("%d/%m/%Y %H:%M")
message = f"📊 Market Decision Report ({now})\n\n"

for symbol, name, code in assets:
    res = get_data(symbol)
    if res:
        price, pct_y, pct_t, drawdown = res
        status = get_status(pct_y)
        advice, ratio = get_advice(drawdown)

        message += (
            f"📌 {name}\n"
            f"{code}\n"
            f"สถานะ: {status}\n"
            f"ราคา: {price:.2f}\n"
            f"เทียบเมื่อวาน: {pct_y:+.2f}%\n"
            f"วันนี้: {pct_t:+.2f}%\n"
            f"ย่อจากจุดสูงสุด: {drawdown:.2f}%\n\n"
            f"💡 คำแนะนำ:\n"
            f"{advice}\n"
            f"สัดส่วนแนะนำ: {ratio} ของเงินลงทุน\n\n"
        )

# =========================
# ส่ง Telegram
# =========================
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)
