import os
import sys
import requests
import yfinance as yf
from datetime import datetime

MODE = sys.argv[1] if len(sys.argv) > 1 else "market"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# พอร์ตของคุณจริง
# =========================
my_portfolio = {
    "GLD": 30000,
    "B-INNOTECH": 11522,
    "K-US500X": 1500,
    "QCOM": 62,
    "BUG": 31
}

# =========================
# Universe ตลาด
# =========================
assets = [
    ("GLD", "SPDR Gold Trust"),
    ("BTC-USD", "Bitcoin"),
    ("SPY", "S&P 500"),
    ("QQQ", "Nasdaq"),
    ("JEPI", "JEPI Income ETF"),
    ("SCHD", "SCHD Dividend ETF"),
]

# =========================
def get_data(symbol):
    data = yf.download(symbol, period="1y", interval="1h", progress=False)
    if len(data) < 2:
        return None
    now_price = data["Close"].iloc[-1].item()
    high_1y = data["Close"].max().item()
    drawdown = (now_price - high_1y) / high_1y * 100
    return now_price, drawdown

def get_weight(drawdown):
    if drawdown < -20: return 5
    elif drawdown < -10: return 4
    elif drawdown < -5: return 3
    elif drawdown < 0: return 2
    else: return 1

# =========================
# ดึงข้อมูลตลาด
# =========================
market = []
for symbol, name in assets:
    res = get_data(symbol)
    if res:
        price, drawdown = res
        market.append({
            "symbol": symbol,
            "name": name,
            "price": price,
            "drawdown": drawdown,
            "weight": get_weight(drawdown)
        })

total_weight = sum(x["weight"] for x in market)

def build_plan(budget):
    plan = []
    for x in market:
        amount = budget * x["weight"] / total_weight
        plan.append({
            "name": x["name"],
            "symbol": x["symbol"],
            "price": x["price"],
            "amount": amount
        })
    return plan

# =========================
# MODE 1: Market Monitor
# =========================
if MODE == "market":
    now = datetime.now().strftime("%H:%M")
    message = f"⏰ Market Update ({now})\n\n"
    for x in market:
        emoji = "📉" if x["drawdown"] < 0 else "📈"
        message += (
            f"{emoji} {x['name']}\n"
            f"ราคา: {x['price']:.2f}\n"
            f"ย่อจากจุดสูงสุด: {x['drawdown']:.2f}%\n\n"
        )

# =========================
# MODE 2: DCA Advisor
# =========================
elif MODE == "dca":
    now = datetime.now().strftime("%d/%m/%Y 12:30")
    message = f"🤖 Personal DCA Advisor\n{now}\n\n"
    message += "พอร์ตของคุณ (สรุป):\n"
    for k, v in my_portfolio.items():
        message += f"- {k}: {v}\n"

    message += "\n🌍 สถานะตลาด:\n"
    for x in market:
        message += f"- {x['name']}: {x['drawdown']:.2f}%\n"

    message += "\n💰 แผนลงทุนวันนี้: 100 บาท\n"
    plan = build_plan(100)
    for p in plan:
        message += (
            f"• {p['name']} ({p['symbol']})\n"
            f"  ราคา: {p['price']:.2f}\n"
            f"  ลงประมาณ: {p['amount']:.0f} บาท\n"
        )

    message += "\n📌 คำแนะนำ:\n"
    message += "ลงทุนเฉพาะตามแผนนี้วันละครั้ง\n"
    message += "นอกเวลา 12:30 ไม่ต้องซื้อเพิ่ม\n"

# =========================
# ส่ง Telegram
# =========================
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={"chat_id": CHAT_ID, "text": message}
)
