import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import add_indicators, pro_signal

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 7000

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC",
    "AUDCAD-OTC"
]

trade_open = False
last_trade_candle = None
last_trade_time = 0

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

print("🔥 BOT CIERRE DE VELA")
send("🔥 BOT CIERRE DE VELA")

# ================= DATOS =================

def get_candles(pair, tf):
    data = iq.get_candles(pair, tf, 100, time.time())
    df = pd.DataFrame(data)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)
    return add_indicators(df)

# ================= ESPERA CIERRE =================

def wait_candle_close():
    while True:
        t = int(iq.get_server_timestamp())
        if t % 60 == 59:  # justo antes del cambio
            time.sleep(0.2)
            return
        time.sleep(0.05)

# ================= TRADE =================

def trade(pair, direction):
    global trade_open, last_trade_time

    status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if status:
        trade_open = True
        last_trade_time = time.time()

        msg = f"🎯 {pair} {direction.upper()} (CIERRE)"
        print(msg)
        send(msg)

# ================= LOOP =================

while True:
    try:
        if trade_open:
            if time.time() - last_trade_time > 65:
                trade_open = False
            else:
                time.sleep(1)
                continue

        wait_candle_close()

        server_time = int(iq.get_server_timestamp())
        current_candle = server_time // 60

        if last_trade_candle == current_candle:
            continue

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            signal = pro_signal(df_m1, df_m5)

            if signal:
                trade(pair, signal)
                last_trade_candle = current_candle
                break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
