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
AMOUNT = 12

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0
pending = None
loss_streak = 0

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

print("🔥 BOT PRO ACTIVO")
send("🔥 BOT PRO ACTIVO")

def get_candles(pair):
    try:
        c = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(c)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction):
    global loss_streak

    status, trade_id = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if status:
        send(f"🔥 {pair} {direction.upper()} $10")

        time.sleep(EXPIRATION * 60 + 2)

        result = iq.check_win_v4(trade_id)

        if result > 0:
            loss_streak = 0
            send("✅ WIN")
        else:
            loss_streak += 1
            send("❌ LOSS")

while True:
    try:
        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # PROTECCIÓN
        if loss_streak >= 2:
            send("⛔ Pausa por racha")
            time.sleep(120)
            loss_streak = 0
            continue

        # ejecutar sniper
        if pending:
            trade(pending[0], pending[1])
            pending = None
            continue

        best = None
        best_score = 0

        for pair in PAIRS:

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
                best = (pair, signal)

        if best and best_score >= 3:
            pending = best
            send(f"📡 {best[0]} {best[1].upper()}")

    except:
        time.sleep(1)
