import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = {}

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

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

print("🔗 Conectado a IQ Option")
send_telegram("🤖 BOT SCANNER IA ACTIVO (1M)")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        print("🔄 Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

def get_open_pairs():
    try:
        all_assets = iq.get_all_open_time()
        pairs = []

        for par, data in all_assets["binary"].items():
            if data["open"]:
                pairs.append(par)

        return pairs

    except:
        return []

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
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
            msg = f"🔥 {pair} {direction.upper()} ($1)"
            print(msg)
            send_telegram(msg)
        else:
            print(f"❌ Falló trade {pair}")

    except Exception as e:
        print("Trade error:", e)

# ================= LOOP =================

while True:
    try:
        reconnect()

        pairs = get_open_pairs()

        if not pairs:
            print("⚠️ No hay pares disponibles")
            time.sleep(2)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in pairs:

            # evitar repetir vela
            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            if signal:
                print(f"📡 {pair} {signal}")
                send_telegram(f"📡 {pair} {signal.upper()}")

                trade(pair, signal)

        time.sleep(0.5)

    except Exception as e:
        print("Error general:", e)
        time.sleep(2)
