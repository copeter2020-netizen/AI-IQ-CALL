import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1090

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

COOLDOWN = 60
last_trade_time = 0

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

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

# ================= DATA =================

def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())

    if not candles:
        return None

    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)
    df = df.sort_values("from")
    df.reset_index(drop=True, inplace=True)

    return df

# ================= TIEMPO =================

def wait_open():
    while True:
        t = iq.get_server_timestamp()
        if t % 60 == 0:
            time.sleep(0.3)
            return
        time.sleep(0.05)

# ================= CONTINUIDAD =================

def bullish_continuation(c):
    body = c['close'] - c['open']
    total = c['high'] - c['low']

    if total == 0:
        return False

    upper_wick = c['high'] - c['close']
    lower_wick = c['open'] - c['low']

    return (
        body > 0 and
        body > total * 0.6 and          # cuerpo dominante
        upper_wick < body * 0.3 and     # poca mecha arriba
        c['close'] >= c['high'] - (total * 0.2)
    )

def bearish_continuation(c):
    body = c['open'] - c['close']
    total = c['high'] - c['low']

    if total == 0:
        return False

    lower_wick = c['close'] - c['low']
    upper_wick = c['high'] - c['open']

    return (
        body > 0 and
        body > total * 0.6
        and lower_wick < body * 0.3
        and c['close'] <= c['low'] + (total * 0.2)
    )

# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN

# ================= TRADE =================

def trade(direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()
        msg = f"🎯 CONTINUIDAD {direction.upper()}"
        print(msg)
        send(msg)

# ================= LOOP =================

print("🚀 BOT CONTINUIDAD ACTIVO")

while True:
    try:
        df = get_candles()
        if df is None:
            continue

        if len(df) < 20:
            continue

        c = df.iloc[-2]  # vela cerrada

        if can_trade():

            # 🟢 CONTINUIDAD ALCISTA
            if bullish_continuation(c):
                send("📈 CONTINUIDAD CALL")
                wait_open()
                trade("call")

            # 🔴 CONTINUIDAD BAJISTA
            elif bearish_continuation(c):
                send("📉 CONTINUIDAD PUT")
                wait_open()
                trade("put")

        time.sleep(0.2)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
