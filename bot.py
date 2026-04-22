import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from estrategia import apply_indicators, trend, strong_bullish, strong_bearish, not_exhausted

# ================= CONFIG =================

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "USDCHF", "EURGBP"]

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1

COOLDOWN = 90  # 🔥 menos trades, más calidad

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_trade_time = 0
last_candle_time = None

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= DATA =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        df = df.sort_values("from")
        df.reset_index(drop=True, inplace=True)

        return df
    except:
        return None

# ================= TIEMPO =================

def wait_open():
    while True:
        t = iq.get_server_timestamp()
        if t % 60 == 0:
            time.sleep(0.2)
            return
        time.sleep(0.05)

# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN

# ================= TRADE =================

def trade(pair, direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()
        msg = f"🎯 {pair} {direction.upper()}"
        print(msg)
        send(msg)

# ================= LOOP =================

print("🚀 BOT PROFESIONAL ACTIVO")

while True:
    try:
        if not can_trade():
            time.sleep(0.5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle_time:
            time.sleep(0.1)
            continue

        last_candle_time = current_candle

        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 50:
                continue

            df = apply_indicators(df)

            c = df.iloc[-2]
            prev = df.iloc[-3]

            t = trend(df)

            # 🟢 BUY SOLO EN TENDENCIA ALCISTA
            if t == "up":
                if strong_bullish(c) and not_exhausted(prev, c):
                    send(f"📈 {pair} CALL (TENDENCIA)")
                    wait_open()
                    trade(pair, "call")
                    break

            # 🔴 SELL SOLO EN TENDENCIA BAJISTA
            elif t == "down":
                if strong_bearish(c) and not_exhausted(prev, c):
                    send(f"📉 {pair} PUT (TENDENCIA)")
                    wait_open()
                    trade(pair, "put")
                    break

        time.sleep(0.1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
