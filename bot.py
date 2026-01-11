import os
import requests
import yfinance as yf
from datetime import datetime

# =========================
# ENV จาก GitHub Secrets
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise ValueError("Missing BOT_TOKEN or CHAT_ID")

# =========================
# Telegram function
# =========================
def send_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": text},
            timeout=10
        )
    except Exception as e:
        print("Telegram error:", e)

# =========================
# Check asset
# =========================
def check_asset(symbol, name, th1, th2):
    data = yf.download(
        symbol,
        period="1y",
        auto_adjust=True,
        progress=False
    )

    if data.empty:
        return f"⚠️ {name}: ดึงข้อมูลไม่ได้"

    close = data["Close"]
    current = float(close.iloc[-1])
    high_1y = float(close.max())

    drop_pct = (current - high_1y) / high_1y * 100

    if drop_pct <= -th2:
        return f"🚨 {name}: ย่อลึก {drop_pct:.2f}% → ลงเพิ่มได้"
    elif drop_pct <= -th1:
        return f"⚠️ {name}: ย่อ {drop_pct:.2f}% → ลงได้บางส่วน"
    elif drop_pct > 0:
        return f"📈 {name}: ทำจุดสูงสุดใหม่ → ไม่ควรไล่ราคา"
    else:
        return f"⏳ {name}: ยังไม่เข้าเงื่อนไข ({drop_pct:.2f}%) → ไม่ควรลง"

# =========================
# MAIN
# =========================
def main():
    today = datetime.now().strftime("%d/%m/%Y")

    sp = check_asset("SPY", "S&P 500 (ตลาดกว้าง)", 10, 15)
    qqq = check_asset("QQQ", "Nasdaq / AI", 10, 15)
    gld = check_asset("GLD", "ทองคำโลก", 5, 8)

    message = (
        f"☀️ รายงานตลาดเช้า {today}\n\n"
        f"{sp}\n"
        f"{qqq}\n"
        f"{gld}"
    )

    send_telegram(message)
    print("Sent report")

if __name__ == "__main__":
    main()
