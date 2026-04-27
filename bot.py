import time
import os
import requests
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair

# =========================
# SILENCIO TOTAL (RAILWAY)
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
AMOUNT = 10  # fijo como pediste

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "USDHKD-OTC",
    "AUDCAD-OTC"
]

last_candle = None
pending_trade = None


# =========================
# TELEGRAM
# =========================
def send(msg):
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

# 🔥 FIX ERROR UNDERLYING (clave)
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 SNIPER ACTIVO")
send("🔥 SNIPER ACTIVO")


# =========================
# FUNCIONES
# =========================
def get_candles(pair):
    try:
        return iq.get_candles(pair, TIMEFRAME, 20, time.time())
    except:
        return None


def is_market_open(pair):
    try:
        data = iq.get_all_open_time()
        return data["digital"][pair]["open"]
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


def wait_open():
    # sincronización exacta con vela
    while int(time.time()) % 60 != 0:
        time.sleep(0.01)


# =========================
# LOOP PRINCIPAL
# =========================
while True:
    try:
        current_candle = int(time.time() // 60)

        # evitar repetir vela
        if current_candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = current_candle

        # =========================
        # EJECUTAR TRADE PENDIENTE
        # =========================
        if pending_trade:
            wait_open()
            execute_trade(pending_trade[0], pending_trade[1])
            pending_trade = None
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        # =========================
        # SCAN MERCADO
        # =========================
        for pair in PAIRS:

            if not is_market_open(pair):
                continue

            candles = get_candles(pair)
            if not candles:
                continue

            data = calculate_indicators(candles)

            signal = check_signal(data)
            if not signal:
                continue

            score = score_pair(data)

            # 🔥 filtro más estricto (clave del winrate)
            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # =========================
        # GENERAR SEÑAL
        # =========================
        if best_pair and best_score >= 4:
            pending_trade = (best_pair, best_signal)
            msg = f"📡 SNIPER {best_pair} {best_signal.upper()} | score {best_score}"
            print(msg)
            send(msg)

    except:
        time.sleep(1)
