import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= VARIABLES =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC"]

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10000

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

last_candle_time = 0

# ================= TELEGRAM =================

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 20:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except:
        return None

# ================= TRADING =================

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            send_telegram(f"✅ {pair} {direction.upper()} ejecutada")
        else:
            send_telegram(f"❌ {pair} error ejecución")

    except:
        send_telegram(f"⚠️ {pair} fallo trade")

# ================= INICIO =================

send_telegram("🤖 BOT ACTIVO")

# ================= LOOP =================

while True:
    try:
        now = int(time.time())

        if now % 60 != 0 or now == last_candle_time:
            time.sleep(0.5)
            continue

        last_candle_time = now

        print("Analizando nueva vela...")

        for pair in PAIRS:
            df = get_candles(pair)

            if df is None:
                continue

            df = calculate_indicators(df)

            if check_buy_signal(df):
                trade("call", pair)

            elif check_sell_signal(df):
                trade("put", pair)

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        send_telegram("⚠️ Error recuperado")
        time.sleep(3)
