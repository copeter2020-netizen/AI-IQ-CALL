import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import check_signal

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 12

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0
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

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    exit()

iq.change_balance("PRACTICE")

# evitar error digital
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT SNIPER PRO ACTIVO")
send("🔥 BOT SNIPER PRO ACTIVO")

# ================= DATA =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 50, time.time())
        df = pd.DataFrame(candles)

        # FIX ERROR 'max'
        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

        return df

    except:
        return None

# ================= TRADE =================

def trade(pair, direction):
    status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if status:
        msg = f"🔥 {pair} → {direction.upper()} (${AMOUNT})"
        print(msg)
        send(msg)

# ================= TIMER SNIPER =================

def wait_next_open():
    while True:
        if int(time.time()) % 60 == 0:
            break
        time.sleep(0.01)

# ================= LOOP =================

while True:
    try:
        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = current_candle

        # ================= EJECUCIÓN SNIPER =================
        if pending:
            wait_next_open()
            trade(pending[0], pending[1])
            pending = None
            continue

        # ================= ANÁLISIS =================

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 20:
                continue

            signal, score = check_signal(df)

            if signal and score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # ================= FILTRO FLEXIBLE (CLAVE) =================

        if best_pair and best_score >= 1:  # 🔥 MÁS ENTRADAS SIN BAJAR CALIDAD
            pending = (best_pair, best_signal)

            msg = f"📡 {best_pair} → {best_signal.upper()} | score: {best_score}"
            print(msg)
            send(msg)

    except:
        time.sleep(1)
