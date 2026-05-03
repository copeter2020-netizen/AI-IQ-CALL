import time
import os
import requests
import pandas as pd
import sys
import logging
from datetime import datetime

from iqoptionapi.stable_api import IQ_Option
from estrategia import add_indicators, high_quality_entry

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 2000

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC",
    "AUDCAD-OTC"
]

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
last_trade_candle = None
loss_streak = 0

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

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO (ALTA CALIDAD)")
send("🔥 BOT ACTIVO (ALTA CALIDAD)")

# ================= DATOS =================

def get_candles(pair, tf):
    try:
        data = iq.get_candles(pair, tf, 100, time.time())
        df = pd.DataFrame(data)

        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        df = add_indicators(df)

        return df
    except:
        return None

# ================= HORARIO =================

def allowed_time():
    hour = datetime.utcnow().hour
    return (6 <= hour <= 11) or (18 <= hour <= 22)

# ================= TRADE =================

def trade(pair, direction):
    global trade_open, last_trade_time

    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            trade_open = True
            last_trade_time = time.time()

            msg = f"🎯 {pair} {direction.upper()}"
            print(msg)
            send(msg)

    except:
        pass

# ================= RESULTADO =================

def check_result():
    global trade_open, loss_streak

    if not trade_open:
        return

    if time.time() - last_trade_time < 65:
        return

    # ⚠️ aquí puedes conectar resultado real
    loss_streak += 1

    trade_open = False

# ================= LOOP =================

while True:
    try:
        check_result()

        if trade_open:
            time.sleep(1)
            continue

        # 🔥 bloqueo por pérdidas
        if loss_streak >= 2:
            send("🛑 BLOQUEADO POR PERDIDAS")
            time.sleep(180)
            loss_streak = 0
            continue

        # 🔥 horario
        if not allowed_time():
            time.sleep(10)
            continue

        server_time = int(iq.get_server_timestamp())
        current_candle = server_time // 60

        if last_trade_candle == current_candle:
            time.sleep(1)
            continue

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            if df_m1 is None or df_m5 is None:
                continue

            signal = high_quality_entry(df_m1, df_m5)

            if signal:
                trade(pair, signal)
                last_trade_candle = current_candle
                break

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
