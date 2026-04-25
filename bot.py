import time
import os
import requests
import pandas as pd
from datetime import datetime

from iqoptionapi.stable_api import IQ_Option
from estrategia import evaluate_pair

# ================= CONFIG =================

PAIRS = [
    "EURUSD", "EURJPY", "GBPUSD",
    "USDCHF", "EURGBP", "AUDUSD",
    "USDJPY", "GBPJPY"
]

TIMEFRAME = 60
EXPIRATION = 5   # 🔥 5 minutos
AMOUNT = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_trade_time = 0

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)

try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        iq.connect()
        iq.change_balance("PRACTICE")

def get_candles(pair):
    candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

    if not candles:
        return None

    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)

    return df

# ================= TRADE =================

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} (5M)"
            print(msg)
            send(msg)
        else:
            print("❌ Falló trade")

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

print("🔥 BOT SCANNER ACTIVO (5M)")
send("🔥 BOT SCANNER 5M ACTIVADO")

# ================= LOOP =================

while True:
    try:
        reconnect()

        best = None

        # 🔍 ESCANEAR TODOS LOS PARES
        for pair in PAIRS:

            df = get_candles(pair)
            if df is None:
                continue

            result = evaluate_pair(df)

            if result is None:
                continue

            if best is None or result["score"] > best["score"]:
                best = {
                    "pair": pair,
                    "score": result["score"],
                    "direction": result["direction"]
                }

        # 🔥 ENTRAR SOLO SI ES BUENA
        if best and best["score"] >= 3:

            now = time.time()

            # evitar sobreoperar
            if now - last_trade_time > 300:

                trade(best["pair"], best["direction"])
                last_trade_time = now

        time.sleep(10)

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
