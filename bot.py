import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair

# 🔇 eliminar spam logs
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 22

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0

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
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")

# ❌ FIX error 'underlying'
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")

# ================= DATOS =================
def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

# ================= TRADE =================
def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)
        if status:
            print(f"🔥 {pair} {direction.upper()}")
            send(f"🔥 {pair} {direction.upper()} ${AMOUNT}")
    except:
        pass

# ================= LOOP PRINCIPAL =================
while True:
    try:
        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        # ⏱️ esperar nueva vela
        if current_candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = current_candle

        best_pair = None
        best_signal = None
        best_score = -2

        # 🔍 analizar pares
        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 5:
                continue

            data = calculate_indicators(df.to_dict("records"))

            signal = check_signal(data)
            if signal is None:
                continue

            score = score_pair(data)

            # 🔥 siempre elegir el mejor (aunque score bajo)
            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # ================= EJECUCIÓN =================
        if best_pair and best_signal:

            print(f"📡 {best_pair} {best_signal.upper()} (score {best_score})")
            send(f"📡 {best_pair} {best_signal.upper()}")

            # ⏱️ entrar justo al inicio de vela
            time.sleep(0.3)

            trade(best_pair, best_signal)

        else:
            print("…sin señal")

    except Exception as e:
        # ❌ evitar spam pero mostrar fallo crítico
        print("Error loop:", e)
        time.sleep(1)
