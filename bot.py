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
AMOUNT = 13

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

pending = None

# =========================
# TELEGRAM
# =========================
def send(msg):
    if not TOKEN or not CHAT_ID:
        return
    try:
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
    exit()

iq.change_balance("PRACTICE")

# FIX ERROR IQ OPTION
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT SNIPER ACTIVO")
send("🔥 BOT SNIPER ACTIVO")

# =========================
# FUNCIONES
# =========================
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


def execute_trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)
        if status:
            msg = f"🚀 {pair} {direction.upper()} ${AMOUNT}"
            print(msg)
            send(msg)
    except:
        pass


def wait_close():
    # esperar cierre real (segundo 59)
    while int(time.time()) % 60 != 59:
        time.sleep(0.01)


def wait_open():
    # esperar apertura real (segundo 0)
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:

        # 🔥 ESPERAR CIERRE DE VELA
        wait_close()

        best_pair = None
        best_signal = None
        best_score = 0

        # 🔍 ANALISIS
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

        # 🎯 EJECUCION SNIPER
        if best_pair and best_score >= 2:
            msg = f"📡 {best_pair} {best_signal.upper()} | score {best_score}"
            print(msg)
            send(msg)

            wait_open()
            execute_trade(best_pair, best_signal)

        else:
            print("…sin señal")

    except:
        time.sleep(1)
