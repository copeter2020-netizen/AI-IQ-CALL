import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

import estrategia
from estrategia import (
    calculate_indicators,
    pre_buy, pre_sell,
    confirm_buy, confirm_sell
)

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_trade_time = 0
COOLDOWN = 60

pending = None
signal_time = 0
MAX_WAIT = 50

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

def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())
    if not candles:
        return None

    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)

    df = df.sort_values("from")
    df.reset_index(drop=True, inplace=True)

    return df


# ================= TRADE =================

def trade(direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()

        msg = f"🎯 EJECUCIÓN {direction.upper()}"
        print(msg)
        send(msg)


# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN


# ================= LOOP =================

print("🚀 BOT LIMPIO ACTIVO")

while True:
    try:
        df = get_candles()
        if df is None:
            continue

        df = calculate_indicators(df)

        # ================= PRE-SEÑAL =================

        if pending is None:
            if pre_buy(df):
                pending = "buy"
                signal_time = time.time()
                send("📍 SEÑAL BUY")

            elif pre_sell(df):
                pending = "sell"
                signal_time = time.time()
                send("📍 SEÑAL SELL")

        # ================= EXPIRACIÓN =================

        if pending and (time.time() - signal_time > MAX_WAIT):
            pending = None

        # ================= CONFIRMACIÓN =================

        if pending == "buy" and confirm_buy(df) and can_trade():
            trade("CALL")
            pending = None

        elif pending == "sell" and confirm_sell(df) and can_trade():
            trade("PUT")
            pending = None

        # 🔇 SILENCIO TOTAL (NO SPAM EN RAILWAY)
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
