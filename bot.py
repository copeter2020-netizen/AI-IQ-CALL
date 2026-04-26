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
from ai_auto import register_trade, allow_trade

# 🔇 silencio total
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1000  # 🔥 monto fijo (sin get_amount)

last_candle = 0
pending = None

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    exit()

iq.change_balance("PRACTICE")

# 🔥 FIX errores OTC
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("✅ BOT SNIPER ACTIVO")
send("✅ BOT SNIPER ACTIVO")

# ================= FUNCIONES =================

def reconnect():
    try:
        if not iq.check_connect():
            iq.connect()
            iq.change_balance("PRACTICE")
    except:
        pass

def get_pairs():
    try:
        data = iq.get_all_open_time()
        return [p for p, i in data["binary"].items() if i["open"]]
    except:
        return []

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            send(f"🔥 {pair} {direction.upper()} (${AMOUNT})")

            # 🔥 resultado simulado
            result = random.choice(["win", "loss"])
            register_trade(result)

    except:
        pass

# ================= LOOP =================

while True:
    try:
        reconnect()

        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # 🔥 EJECUCIÓN SNIPER (siguiente vela)
        if pending:
            pair, direction = pending
            trade(pair, direction)
            pending = None
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in get_pairs():

            df = get_candles(pair)
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
                best_score = score
                best_pair = pair
                best_signal = signal

        # 🔥 guardar señal para siguiente vela
        if best_pair and best_score >= 2:
            pending = (best_pair, best_signal)
            send(f"📡 SNIPER READY\n{best_pair} {best_signal.upper()}")

    except:
        time.sleep(1)
