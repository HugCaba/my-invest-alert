import os
import sys
import requests
import yfinance as yf
from datetime import datetime

MODE = sys.argv[1] if len(sys.argv) > 1 else "market"

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# =========================
# กองทุนไทย (ใส่มือวันละครั้ง)
# =========================
thai_funds = {
    "B-INNOTECH": 11.52,
    "K-US500X": 1.50
}

# =========================
# พอร์ตของคุณ
# =========================
my_portfolio = {
    "GLD": {"name": "SPDR Gold Trust", "type": "api"},
    "QCOM": {"name": "Qualcomm", "type": "api"},
    "BUG": {"name": "Global X Cybersecurity ETF", "type": "api"},
    "B-INNOTECH": {"name": "B-INNOTECH HRMF", "type": "thai"},
    "K-US500X": {"name": "K-US500X-A", "type": "thai"}
}

# =========================
# ตลาดรวม
# =========================
market_assets = [
    ("SPY", "S&P 500", "US500"),
    ("QQQ", "Nasdaq", "NASDAQ"),
    ("GLD", "SPDR Gold Trust", "GLD"),
    ("BTC-USD", "Bitcoin", "BTC/USD"),
]

# =========================
def get_data(symbol):
    data = yf.download(symbol, period="2d", interval="1h", progress=False)
    if len(data) < 2:
        return None

    now_price = data["Close"].iloc[-1].item()
    yesterday_close = data["Close"].iloc[0].item()

    today_data = data[data.index.date == data.index[-1].date()]
    today_open = today_data["Open"].iloc[0].item()

    pct_y = (now_price - yesterday_close) / yesterday_close * 100
    pct_t = (now_price - today_open) / today_open * 100

    hist = yf.download(symbol, period="1y", progress=False)
    high_1y = hist["Close"].max().item()
    drawdown = (now_price - high_1y) / high_1y * 100

    return now_price, pct_y, pct_t, drawdown

def get_status(pct):
    if pct > 1:
        return "🟢 ปกติ"
    elif pct < -1:
        return "🔴 อ่อนแรง"
    else:
        return "🟡 แกว่งตัว"

def get_advice(drawdown):
    if drawdown < -10:
        return "ควรลงเพิ่ม"
    elif drawdown < -5:
        return "รอได้"
    else:
        return "ยังไม่ควรลง"

# =========================
# MODE: Market Update
# =========================
if MODE == "market":
    now = datetime.now().strftime("%H:%M")
    message = f"📊 Market Update + My Portfolio (Hybrid)\n{now}\n\n"

    message += "🌍 ตลาดรวม\n"
    for symbol, name, code in market_assets:
        res = get_data(symbol)
        if res:
            price, pct_y, pct_t, drawdown = res
            status = get_status(pct_y)
            advice = get_advice(drawdown)

            message += (
                f"📌 {name}\n"
                f"{code}\n"
                f"สถานะ: {status}\n"
                f"ราคา: {price:.2f}\n"
                f"เทียบเมื่อวาน: {pct_y:+.2f}%\n"
                f"วันนี้: {pct_t:+.2f}%\n"
                f"ย่อจากจุดสูงสุด: {drawdown:.2f}%\n"
                f"คำแนะนำ: {advice}\n\n"
            )

    message += "💼 พอร์ตของฉัน\n"
    for symbol, info in my_portfolio.items():
        if info["type"] == "api":
            res = get_data(symbol)
            if res:
                price, pct_y, pct_t, drawdown = res
                status = get_status(pct_y)
                advice = get_advice(drawdown)

                message += (
                    f"📌 {info['name']}\n"
                    f"{symbol}\n"
                    f"สถานะ: {status}\n"
                    f"ราคา: {price:.2f}\n"
                    f"เทียบเมื่อวาน: {pct_y:+.2f}%\n"
                    f"วันนี้: {pct_t:+.2f}%\n"
                    f"ย่อจากจุดสูงสุด: {drawdown:.2f}%\n"
                    f"คำแนะนำ: {advice}\n\n"
                )
        else:
            nav = thai_funds.get(symbol, None)
            message += (
                f"📌 {info['name']}\n"
                f"{symbol}\n"
                f"สถานะ: ⚪ กองทุนไทย\n"
                f"NAV ล่าสุด: {nav}\n"
                f"คำแนะนำ: ใช้เพื่อ DCA ระยะยาว\n\n"
            )

# =========================
# MODE: DCA (12:30)
# =========================
elif MODE == "dca":
    now = datetime.now().strftime("%d/%m/%Y 12:30")
    market = []
    for symbol, name, code in market_assets:
        res = get_data(symbol)
        if res:
            price, pct_y, pct_t, drawdown = res
            market.append({
                "symbol": symbol,
                "name": name,
                "code": code,
                "price": price,
                "pct_y": pct_y,
                "pct_t": pct_t,
                "drawdown": drawdown,
                "status": get_status(pct_y),
            })

    best = sorted(market, key=lambda x: x["drawdown"])[0]

    message = (
        f"🤖 DCA วันนี้ (Hybrid)\n{now}\n\n"
        f"🎯 ตัวที่ควรลงมากที่สุด:\n"
        f"{best['name']} ({best['code']})\n\n"
        f"สถานะ: {best['status']}\n"
        f"ราคา: {best['price']:.2f}\n"
        f"เทียบเมื่อวาน: {best['pct_y']:+.2f}%\n"
        f"วันนี้: {best['pct_t']:+.2f}%\n"
        f"ย่อจากจุดสูงสุด: {best['drawdown']:.2f}%\n\n"
        f"💰 ลง {best['name']} 100 บาท\n"
    )

# =========================
# ส่ง Telegram
# =========================
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={"chat_id": CHAT_ID, "text": message}
)
