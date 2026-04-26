import time
import os
import requests
import pandas as pd
import sys
import logging
import random

from datetime import datetime, timezone
from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair
from ai_auto import get_amount, register_trade, allow_trade

# 🔇 silencio total
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1

last_candle = 0
pending = None

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("✅ PRICE ACTION SNIPER")
send("✅ PRICE ACTION SNIPER")

def get_pairs():
    data = iq.get_all_open_time()
    return [p for p, i in data["binary"].items() if i["open"]]

def candles(pair):
    try:
        c = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(c)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction):
    amount = get_amount()

    status, _ = iq.buy(amount, pair, direction, EXPIRATION)

    if status:
        send(f"🔥 {pair} {direction.upper()} ${amount}")

        result = random.choice(["win", "loss"])
        register_trade(result)

while True:
    try:
        t = iq.get_server_timestamp()
        candle = t // 60

        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # ejecutar sniper
        if pending:
            pair, direction = pending
            trade(pair, direction)
            pending = None
            continue

        best = None
        best_signal = None
        best_score = 0

        for pair in get_pairs():

            df = candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)

            signal = check_signal(df)
            if not signal:
                continue

            score = score_pair(df)

            if not allow_trade(score):
                continue

            if score > best_score:
                best = pair
                best_signal = signal
                best_score = score

        if best:
            pending = (best, best_signal)
            send(f"📡 SNIPER\n{best} {best_signal.upper()}")

    except:
        time.sleep(1)
