import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import check_signal, score_pair  # ❌ quitamos calculate_indicators

# 🔇 eliminar spam logs
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 350

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0
pending = None  # 🔥 para entrada en siguiente vela

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

# FIX OTC error
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")

# ================= DATOS =================
def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)

        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

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

# ================= ESPERAR APERTURA =================
def wait_open():
    while True:
        if int(iq.get_server_timestamp()) % 60 == 0:
            time.sleep(0.05)
            return
        time.sleep(0.002)

# ================= LOOP PRINCIPAL =================
while True:
    try:
        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        # ⏱️ esperar nueva vela
        if current_candle == last_candle:
            time.sleep(0.1)
            continue

        last_candle = current_candle

        # ================= EJECUTAR EN APERTURA =================
        if pending:
            wait_open()
            trade(pending[0], pending[1])
            pending = None
            continue

        best_pair = None
        best_signal = None
        best_score = 0  # 🔥 corregido

        # 🔍 analizar pares
        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 10:
                continue

            signal, score = check_signal(df)  # 🔥 ahora devuelve 2 valores

            if not signal:
                continue

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # ================= FILTRO PRO =================
        if best_pair and best_score >= 3:

            pending = (best_pair, best_signal)  # 🔥 sniper siguiente vela

            print(f"📡 {best_pair} {best_signal.upper()} (score {best_score})")
            send(f"📡 {best_pair} {best_signal.upper()} | score {best_score}")

        else:
            print("…sin señal")

    except Exception as e:
        print("Error loop:", e)
        time.sleep(1)
