import time
import os
import requests
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
AMOUNT = 100

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

pending = None


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


# ================= CONEXION =================
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    exit()

iq.change_balance("PRACTICE")

# FIX IQ ERROR
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 SNIPER OPERATIVO")
send("🔥 SNIPER OPERATIVO")


# ================= FUNCIONES =================
def get_candles(pair):
    try:
        return iq.get_candles(pair, TIMEFRAME, 50, time.time())
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
            send(f"🚀 {pair} {direction.upper()} ${AMOUNT}")
    except:
        pass


def wait_close():
    # esperar cierre REAL de vela (segundo 59)
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


def wait_open():
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# ================= LOOP =================
while True:
    try:

        # 🔥 1. ESPERAR CIERRE DE VELA
        wait_close()

        best = None
        best_score = 0

        # 🔥 2. ANALIZAR JUSTO AL CIERRE
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

            # 🔥 MENOS ESTRICTO PERO INTELIGENTE
            if score > best_score:
                best_score = score
                best = (pair, signal)

        # 🔥 3. SI HAY SEÑAL → EJECUTAR SIGUIENTE VELA
        if best and best_score >= 2:
            send(f"📡 {best[0]} {best[1].upper()} | score {best_score}")

            wait_open()  # entrada exacta

            trade(best[0], best[1])

        else:
            # opcional: ver que sí está analizando
            print("…sin señal")

    except:
        time.sleep(1)
