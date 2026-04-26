import time
import os
import requests
import pandas as pd
import sys
import logging

from datetime import datetime
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_signal, score_pair

# 🔇 quitar spam
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

# ================= CONFIG =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
RISK_PERCENT = 3  # 3%

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
    print("❌ Error conexión")
    exit()

# 👉 CAMBIA A REAL SI QUIERES DINERO REAL
iq.change_balance("PRACTICE")

# evitar errores OTC
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("✅ BOT OPERATIVO")
send("✅ BOT OPERATIVO")

# ================= FUNCIONES =================

def get_balance():
    try:
        return iq.get_balance()
    except:
        return 0

def get_amount():
    balance = get_balance()
    return round(balance * RISK_PERCENT, 2)

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
    amount = get_amount()

    status, trade_id = iq.buy(amount, pair, direction, EXPIRATION)

    if status:
        send(f"🔥 TRADE\n{pair} {direction.upper()} ${amount}")

        # esperar resultado real
        time.sleep(EXPIRATION * 60 + 2)

        result = iq.check_win_v4(trade_id)

        if result > 0:
            send(f"✅ WIN {pair}")
        else:
            send(f"❌ LOSS {pair}")

# ================= LOOP =================

while True:
    try:
        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # 🔥 EJECUTAR ENTRADA (SIGUIENTE VELA)
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

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # 🔥 guardar señal (SNIPER)
        if best_pair and best_score >= 2:
            pending = (best_pair, best_signal)
            send(f"📡 SEÑAL\n{best_pair} {best_signal.upper()}")

    except Exception as e:
        time.sleep(1)
