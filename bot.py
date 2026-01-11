import requests
import yfinance as yf
from datetime import datetime

BOT_TOKEN = "8444957235:AAF9FDV3cx_p5H1RRrOXNI7xwwdSMjZoOJg"
CHAT_ID = "6744596307"

def check_asset(symbol, name, th_start, th_deep):
    data = yf.download(
        symbol,
        period="1y",
        auto_adjust=True,
        progress=False
    )
    if data.empty:
        return f"⚠️ {name}: ดึงข้อมูลไม่ได้"

    current = data['Close'].iloc[-1].item()
    high_1y = data['Close'].max().item()
    drop_pct = (current - high_1y) / high_1y * 100

    if drop_pct <= -th_deep:
        return f"🚨 {name}: ย่อลึก {drop_pct:.2f}% → จังหวะดี"
    elif drop_pct <= -th_start:
        return f"⚠️ {name}: ย่อ {drop_pct:.2f}% → เริ่มสะสม"
    else:
        return f"⏳ {name}: ยังไม่เข้าเงื่อนไข ({drop_pct:.2f}%)"

# เช็กสินทรัพย์
sp500 = check_asset("SPY", "S&P 500 (ตลาดกว้าง)", 10, 15)
nasdaq = check_asset("QQQ", "Nasdaq / AI", 10, 15)
gold = check_asset("GLD", "ทองคำโลก", 5, 8)

today = datetime.now().strftime("%d/%m/%Y")

message = (
    f"☀️ รายงานตลาดเช้า {today}\n\n"
    f"{sp500}\n"
    f"{nasdaq}\n"
    f"{gold}"
)

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {"chat_id": CHAT_ID, "text": message}
requests.post(url, data=payload)
