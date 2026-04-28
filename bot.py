# bot.py

import time
import os
import requests
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair

# =========================
# SILENCIO (RAILWAY)
# =========================
logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC", 
    "EURCHF-OTC", 
    "AUDCAD-OTC"
]

# =========================
# TELEGRAM
# =========================
def send(msg):
    try:
        if TOKEN and CHAT_ID:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
    except:
        pass

# =========================
# CONEXION
# =========================
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión")
    exit()

iq.change_balance("PRACTICE")

# FIX ERROR IQ
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")

# =========================
# FUNCIONES
# =========================
def get_candles(pair):
    try:
        return iq.get_candles(pair, TIMEFRAME, 50, iq.get_server_timestamp())
    except:
        return None


def is_open(pair):
    try:
        return iq.get_all_open_time()["digital"][pair]["open"]
    except:
        return False


def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)
        if status:
            msg = f"🚀 {pair} {direction.upper()} ${AMOUNT}"
            print(msg)
            send(msg)
    except:
        pass


# =========================
# LOOP PRINCIPAL
# =========================
last_candle = None

while True:
    try:
        server_time = int(iq.get_server_timestamp())
        candle_time = server_time // 60

        # detectar nueva vela REAL
        if candle_time != last_candle:

            last_candle = candle_time

            best_pair = None
            best_signal = None
            best_score = 0

            print("🔍 Analizando...")

            for pair in PAIRS:

                if not is_open(pair):
                    continue

                candles = get_candles(pair)
                if not candles:
                    continue

                data = calculate_indicators(candles)

                signal = check_signal(data)
                if not signal:
                    continue

                score = score_pair(data)

                if score > best_score:
                    best_score = score
                    best_pair = pair
                    best_signal = signal

            # 🔥 MENOS ESTRICTO → MÁS ENTRADAS
            if best_pair and best_score >= 1:

                msg = f"📡 {best_pair} {best_signal.upper()} | score {best_score}"
                print(msg)
                send(msg)

                # esperar apertura exacta
                while int(iq.get_server_timestamp()) % 60 != 0:
                    time.sleep(0.01)

                trade(best_pair, best_signal)

            else:
                print("…sin señal")

        time.sleep(0.2)

    except:
        time.sleep(1)
