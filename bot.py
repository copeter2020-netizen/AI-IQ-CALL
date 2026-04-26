import time
import os
import requests
import pandas as pd
import random
import sys
import logging

from datetime import datetime, timezone
from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair
from ai_auto import allow_trade, register_trade

# ================= 🔇 SILENCIAR LOGS =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 12

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔥 SOLO PARES REALES (SIN OTC)
VALID_PAIRS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    "USDCAD", "USDCHF", "NZDUSD", "EURJPY",
    "GBPJPY", "EURGBP"
]

last_candle = 0

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

# ================= HORARIO =================

def is_trading_time():
    now = datetime.now(timezone.utc)
    bogota_hour = (now.hour - 5) % 24
    return 7 <= bogota_hour <= 11

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    exit()

iq.change_balance("PRACTICE")

# 🔥 FIX DIGITAL
iq.get_digital_underlying_list_data = lambda: {"underlying": []}
iq.subscribe_strike_list = lambda *args, **kwargs: None
iq.unsubscribe_strike_list = lambda *args, **kwargs: None

print("✅ CONECTADO")

# ================= FUNCIONES =================

def reconnect():
    try:
        if not iq.check_connect():
            iq.connect()
            iq.change_balance("PRACTICE")
    except:
        pass

def get_pairs():
    # 🔥 SOLO USA LISTA LIMPIA
    return VALID_PAIRS

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 200, time.time())
        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            print(f"🔥 {pair} {direction.upper()}")
            send_telegram(f"🔥 {pair} {direction.upper()}")

            result = random.choice(["win", "loss"])
            register_trade(pair, direction, result)

    except:
        pass

# ================= LOOP =================

while True:
    try:
        reconnect()

        if not is_trading_time():
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = current_candle

        pairs = get_pairs()

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in pairs:

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

        if best_pair and best_score >= 3:
            print(f"📡 {best_pair} {best_signal.upper()}")
            send_telegram(f"📡 {best_pair} {best_signal.upper()}")
            trade(best_pair, best_signal)

        time.sleep(0.5)

    except:
        time.sleep(1)
