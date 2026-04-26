import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
RISK = 0.03

last_candle = 0
pending_trades = []

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

print("✅ BOT ACTIVO")

def get_balance():
    return iq.get_balance()

def get_amount():
    return round(get_balance() * RISK, 2)

def get_pairs():
    data = iq.get_all_open_time()
    return [p for p, i in data["binary"].items() if i["open"]]

def get_candles(pair):
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

while True:
    try:
        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # 🔥 ejecutar todas las pendientes
        for pair, direction in pending_trades:
            trade(pair, direction)

        pending_trades.clear()

        # 🔍 detectar señales
        signals = []

        for pair in get_pairs():

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)

            signal = check_signal(df)
            if not signal:
                continue

            score = score_pair(df)

            if score >= 1:  # 🔥 más flexible
                signals.append((pair, signal))

        # guardar TODAS para siguiente vela
        if signals:
            pending_trades = signals
            send(f"📡 {len(signals)} señales detectadas")

    except:
        time.sleep(1)
