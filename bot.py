import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 10000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_trade_time = 0
COOLDOWN = 60

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

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


# ================= CANDLES =================

def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())

    if not candles:
        return None

    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)

    df = df.sort_values("from")
    df.reset_index(drop=True, inplace=True)

    return df


# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN


def trade(direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()
        print("TRADE:", direction)
        send_telegram(f"📊 {PAIR} {direction.upper()}")


# ================= LOOP =================

print("🚀 BOT STRUCTURE LIVE ACTIVO (OHLC + S/R)")

while True:
    try:
        df = get_candles()
        if df is None:
            continue

        df = calculate_indicators(df)

        buy = check_buy_signal(df)
        sell = check_sell_signal(df)

        print("BUY:", buy, "SELL:", sell)

        if buy and can_trade():
            trade("call")

        elif sell and can_trade():
            trade("put")

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
