import os
import requests
import yfinance as yf
from datetime import datetime

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

assets = [
    ("SPY", "⏳ S&P 500 (ตลาดกว้าง)"),
    ("QQQ", "📊 Nasdaq / AI"),
    ("GLD", "🥇 ทองคำ (GLD)"),
    ("GC=F", "🏅 Gold Futures"),
    ("BTC-USD", "₿ Bitcoin"),
]

def get_change(symbol):
    data = yf.download(
        symbol,
        period="2d",
        interval="1h",
        progress=False
    )

    if len(data) < 2:
        return None

    now_price = data["Close"].iloc[-1]
    yesterday_close = data["Close"].iloc[0]

    # หา open ของวันนี้ (แท่งแรกของวัน)
    today_data = data[data.index.date == data.index[-1].date()]
    today_open = today_data["Open"].iloc[0]

    pct_from_yesterday = (now_price - yesterday_close) / yesterday_close * 100
    pct_today = (now_price - today_open) / today_open * 100

    return pct_from_yesterday, pct_today

lines = []
for symbol, name in assets:
    res = get_change(symbol)
    if res:
        pct_y, pct_t = res

        if pct_y > 0:
            trend = "📈"
        else:
            trend = "📉"

        lines.append(
            f"{trend} {name}: "
            f"เมื่อวาน {pct_y:+.2f}% | วันนี้ {pct_t:+.2f}%"
        )

now = datetime.now().strftime("%H:%M")

message = f"📊 Market Snapshot ({now})\n\n"
for line in lines:
    message += line + "\n"

# ส่ง Telegram
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)
