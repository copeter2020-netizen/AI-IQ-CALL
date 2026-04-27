import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair

# 🔇 eliminar spam
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 10  # 🔥 fijo 10 USD

# 🎯 SOLO ESTOS PARES
PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0
pending = []

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión")
    exit()

iq.change_balance("PRACTICE")  # 👉 cambia a REAL si quieres

# fix errores OTC
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("✅ BOT OTC ACTIVO (6 PARES)")
send("✅ BOT OTC ACTIVO (6 PARES)")

# ================= FUNCIONES =================

def get_candles(pair):
    try:
        c = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(c)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction):
    status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if status:
        send(f"🔥 {pair} {direction.upper()} $10")

# ================= LOOP =================

while True:
    try:
        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        # 🔥 SOLO AL CIERRE
        if candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = candle

        # 🔥 ejecutar pendientes
        for pair, direction in pending:
            trade(pair, direction)

        pending.clear()

        signals = []

        for pair in PAIRS:

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)

            signal = check_signal(df)
            if not signal:
                continue

            score = score_pair(df)

            # 🔥 filtro equilibrado
            if score >= 2:
                signals.append((pair, signal, score))

        # ordenar mejores
        signals = sorted(signals, key=lambda x: x[2], reverse=True)

        # máximo 2 entradas por vela
        selected = signals[:2]

        if selected:
            pending = [(p, s) for p, s, sc in selected]
            send(f"📡 {len(selected)} setups listos")

    except:
        time.sleep(1)
