import os
import requests
import yfinance as yf
from datetime import datetime
import openai

# =========================
# Secrets
# =========================
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
openai.api_key = os.environ["OPENAI_API_KEY"]

# =========================
# พอร์ตของคุณ (จากรูปจริง)
# =========================
my_portfolio_value = {
    "GLD": 31589,
    "QCOM": 1949,
    "BUG": 987,
    "B-INNOTECH": 11522,
    "K-US500X": 1500
}

# =========================
# Universe ตลาด
# =========================
assets = [
    ("BTC-USD", "Bitcoin", "BTC/USD"),
    ("QQQ", "Nasdaq", "NASDAQ"),
    ("SPY", "S&P 500", "US500"),
    ("GLD", "SPDR Gold Trust", "GLD"),
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

def score_asset(drawdown, pct_today, portfolio_weight):
    score = 0
    score += abs(drawdown) * 1.5
    if pct_today < 0:
        score += abs(pct_today) * 2
    score += (1 / (portfolio_weight + 0.1)) * 5
    return score

# =========================
# วิเคราะห์ตลาด
# =========================
market = []
total_portfolio = sum(my_portfolio_value.values())

for symbol, name, code in assets:
    res = get_data(symbol)
    if res:
        price, pct_y, pct_t, drawdown = res
        port_value = my_portfolio_value.get(symbol, 0)
        port_weight = port_value / total_portfolio

        score = score_asset(drawdown, pct_t, port_weight)

        market.append({
            "symbol": symbol,
            "name": name,
            "code": code,
            "price": price,
            "pct_y": pct_y,
            "pct_t": pct_t,
            "drawdown": drawdown,
            "score": score
        })

# =========================
# เลือก Top 3
# =========================
top3 = sorted(market, key=lambda x: x["score"], reverse=True)[:3]
total_score = sum(x["score"] for x in top3)

# =========================
# สร้างข้อความให้ AI
# =========================
top3_text = ""
for i, x in enumerate(top3, 1):
    top3_text += (
        f"#{i} {x['name']} ({x['code']}) | "
        f"ราคา {x['price']:.2f} | "
        f"เมื่อวาน {x['pct_y']:+.2f}% | "
        f"วันนี้ {x['pct_t']:+.2f}% | "
        f"ย่อจากจุดสูงสุด {x['drawdown']:.2f}%\n"
    )

budget = 500  # เปลี่ยนเป็น 100 / 300 / 500 / 1000 ได้
budget_text = ""
for x in top3:
    portion = budget * x["score"] / total_score
    budget_text += f"- {x['name']}: {portion:.0f} บาท\n"

portfolio_text = ""
for k, v in my_portfolio_value.items():
    portfolio_text += f"- {k}: {v} บาท\n"

market_text = ""
for x in market:
    market_text += (
        f"{x['name']} | ราคา {x['price']:.2f} | "
        f"วันนี้ {x['pct_t']:+.2f}% | "
        f"ย่อจากจุดสูงสุด {x['drawdown']:.2f}%\n"
    )

# =========================
# เรียก AI
# =========================
def ai_analyze():
    prompt = f"""
คุณเป็นผู้ช่วยวิเคราะห์การลงทุนส่วนตัว

ข้อมูลตลาด:
{market_text}

Top 3 วันนี้:
{top3_text}

งบประมาณวันนี้:
{budget_text}

พอร์ตของฉัน:
{portfolio_text}

ช่วยเขียนข้อความสำหรับ Telegram:
1. บอกว่าวันนี้ควรลงอะไร
2. บอกว่างบควรแบ่งอย่างไร
3. สรุปภาพรวมตลาด + คำเตือน

เขียนเป็นภาษาไทย
โทนเหมือนนักวิเคราะห์การเงิน
สั้น กระชับ ใช้งานได้จริง
"""
    response = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"]

ai_text = ai_analyze()

# =========================
# ส่ง Telegram
# =========================
now = datetime.now().strftime("%d/%m/%Y 12:30")
message = f"""🤖 DCA วันนี้ (Top 3)
{now}

{ai_text}
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
requests.post(
    url,
    data={"chat_id": CHAT_ID, "text": message}
)
