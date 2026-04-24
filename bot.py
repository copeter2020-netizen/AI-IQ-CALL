import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import detect_block_signal

# ================= CONFIG =================

PAIRS = ["EURUSD", "EURJPY", "GBPUSD", "USDCHF", "EURGBP"]

TIMEFRAME = 60       # velas de 1 minuto
EXPIRATION = 30      # 30 minutos
AMOUNT = 1           # $1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_block = None
pending_signal = None

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

# 🔥 eliminar error underlying
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

def get_block_candles(pair):
    candles = iq.get_candles(pair, 60, 60, time.time())

    if not candles or len(candles) < 30:
        return None

    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)

    return df.tail(30)

def get_block_id():
    now = datetime.now(timezone.utc)
    return (now.hour, now.minute // 30)

# ================= TRADE =================

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} 30M"
            print(msg)
            send(msg)
        else:
            print("❌ Falló trade")

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

print("🔥 BOT TII 30M REAL ACTIVO")
send("🔥 BOT TII 30M REAL ACTIVADO")

# ================= LOOP =================

while True:
    try:
        reconnect()

        current_block = get_block_id()

        # NUEVO BLOQUE
        if current_block != last_block:

            last_block = current_block

            # 🔥 EJECUTAR OPERACIÓN
            if pending_signal:
                pair, direction = pending_signal
                trade(pair, direction)
                pending_signal = None

            # 🔍 ANALIZAR BLOQUE QUE TERMINÓ
            for pair in PAIRS:

                df = get_block_candles(pair)
                if df is None:
                    continue

                signal = detect_block_signal(df)

                if signal:
                    pending_signal = (pair, signal)
                    send(f"📊 {pair} {signal.upper()} DETECTADO → SIGUIENTE BLOQUE")
                    break

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
