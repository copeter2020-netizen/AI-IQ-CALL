import time
import os
import pandas as pd
from datetime import datetime

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal
from ai_auto import predict

# ================= CONFIG =================

AMOUNT = 1
TIMEFRAME = 60
EXPIRATION = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)

# 🔥 FIX ERROR UNDERLYING
iq.api.digital_option = None
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

iq.connect()
iq.change_balance("PRACTICE")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        iq.connect()
        iq.change_balance("PRACTICE")

def get_all_pairs():
    try:
        assets = iq.get_all_open_time()
        pairs = []

        for pair, data in assets["digital"].items():
            if "OTC" in pair and data["open"]:
                pairs.append(pair)

        return pairs
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
            print(f"🔥 TRADE {pair} {direction}")
        else:
            print(f"❌ Falló {pair}")

    except Exception as e:
        print("Error trade:", e)

# ================= BOT =================

print("🔥 BOT SCANNER IA LIGERA ACTIVO")

last_candle = {}

while True:
    try:
        reconnect()

        pairs = get_all_pairs()

        for pair in pairs:

            server_time = iq.get_server_timestamp()
            candle_time = server_time // 60

            if pair in last_candle and last_candle[pair] == candle_time:
                continue

            last_candle[pair] = candle_time

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            # 🔥 IA DECIDE SI OPERAR
            if signal and predict():

                print(f"📊 {pair} señal {signal}")

                trade(pair, signal)

                # 🔥 SOLO UNA OPERACIÓN POR CICLO
                break

        time.sleep(1)

    except Exception as e:
        print("Error general:", e)
        time.sleep(2)
