import sys
import os
import requests
import yfinance as yf
from datetime import datetime

# ===== Telegram ENV =====
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

# ===== Mode =====
mode = sys.argv[1] if len(sys.argv) > 1 else "market"

# ===== พอร์ตของคุณ =====
my_portfolio = {
    "GLD": "GLD",
    "B-INNOTECH": "B-INNOTECH.BK",
    "K-US500X": "K-US500X.BK",
    "QCOM": "QCOM",
    "BUG": "BUG"
}

# ===== Helper =====
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_price(symbol):
    data = yf.download(symbol, period="2d", progress=False)

    if data is None or len(data) < 2:
        return None

    # รองรับทั้ง single และ multi column
    close_today = data["Close"].iloc[-1]
    close_yesterday = data["Close"].iloc[-2]

    if hasattr(close_today, "values"):
        today = float(close_today.values[0])
        yesterday = float(close_yesterday.values[0])
    else:
        today = float(close_today)
        yesterday = float(close_yesterday)

    pct_today = (today - yesterday) / yesterday * 100
    return today, pct_today

def get_status(pct):
    if pct > 1:
        return "🟢 แข็งแรง"
    elif pct > 0:
        return "🟡 บวกเล็กน้อย"
    elif pct > -1:
        return "🟠 อ่อนตัว"
    else:
        return "🔴 อ่อนแรง"

def get_action(pct):
    if pct > 1:
        return "ไม่ควรไล่ซื้อ"
    elif pct > 0:
        return "ถือไว้"
    elif pct > -1:
        return "ปล่อยไว้ก่อน"
    else:
        return "เหมาะกับการ DCA เพิ่ม"

# =========================
# MARKET MODE
# =========================
def run_market_mode():
    market_assets = {
        "S&P500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Bitcoin": "BTC-USD",
        "Gold": "GLD"
    }

    msg = f"⏰ Market Update {datetime.now().strftime('%H:%M')}\n\n"

    for name, symbol in market_assets.items():
        res = get_price(symbol)
        if res:
            price, pct_today = res
            status = get_status(pct_today)
            action = get_action(pct_today)
            msg += (
                f"{name} | {price:.2f} | "
                f"วันนี้ {pct_today:.2f}% | "
                f"{status} | แนะนำ: {action}\n"
            )

    msg += "\n📊 Portfolio Monitor\n"

    for name, symbol in my_portfolio.items():
        res = get_price(symbol)
        if res:
            price, pct_today = res
            status = get_status(pct_today)
            action = get_action(pct_today)
            msg += (
                f"{name} | {price:.2f} | "
                f"วันนี้ {pct_today:.2f}% | "
                f"{status} | แนะนำ: {action}\n"
            )

    send_telegram(msg)

# =========================
# DCA MODE (AI)
# =========================
def run_dca_mode():
    from openai import OpenAI
    client = OpenAI()

    assets = {
        "S&P500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Bitcoin": "BTC-USD",
        "Gold": "GLD"
    }

    market_data = ""
    for name, symbol in assets.items():
        res = get_price(symbol)
        if res:
            price, pct_today = res
            market_data += f"{name}: วันนี้ {pct_today:.2f}%\n"

    portfolio_text = ""
    for name in my_portfolio.keys():
        portfolio_text += f"{name}\n"

    prompt = f"""
คุณคือ AI ผู้ช่วยวางแผนลงทุนแบบ DCA ระยะยาว

ข้อมูลตลาดวันนี้:
{market_data}

พอร์ตของฉันปัจจุบัน:
{portfolio_text}

โจทย์:
1. วิเคราะห์ว่าพอร์ตฉันควรเพิ่มอะไร หรือไม่ควรเพิ่มอะไร
2. เสนอแผนลงทุน 2 แบบ:
   - งบแบบเบา: 0–500 บาท
   - งบแบบหนัก: 500–1000 บาท
3. จัดอันดับ Top 3 ที่ควรลงทุน
4. บอกจำนวนเงินแต่ละตัว
5. ให้เหตุผลสั้น ๆ

ตอบเป็นภาษาไทย กระชับ ชัดเจน
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    ai_text = response.output_text

    msg = (
        f"🤖 DCA วันนี้ (Top 3)\n"
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"{ai_text}"
    )

    send_telegram(msg)

# ===== RUN =====
if mode == "market":
    run_market_mode()
elif mode == "dca":
    run_dca_mode()
else:
    send_telegram("❌ ไม่รู้จักโหมดที่เรียกใช้")
