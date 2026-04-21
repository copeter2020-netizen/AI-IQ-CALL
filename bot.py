import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 2000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOOKBACK = 30
ZONE_TOL = 0.0006

last_trade_time = 0
COOLDOWN = 60

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


# ================= SOPORTE / RESISTENCIA =================

def get_zones(df):
    recent = df.iloc[-LOOKBACK:]
    support = recent['low'].min()
    resistance = recent['high'].max()
    return support, resistance


# ================= TIEMPO =================

def near_close():
    server_time = iq.get_server_timestamp()
    return server_time % 60 >= 55


# ================= MICRO RECHAZO =================

def rejection_buy(c):
    body = abs(c['close'] - c['open'])
    wick = (c['open'] - c['low']) if c['close'] > c['open'] else (c['close'] - c['low'])
    return wick > body


def rejection_sell(c):
    body = abs(c['close'] - c['open'])
    wick = (c['high'] - c['close']) if c['close'] < c['open'] else (c['high'] - c['open'])
    return wick > body


# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN


# ================= TRADE =================

def trade(direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()
        msg = f"⚡ TRADE {direction.upper()}"
        print(msg)
        send(msg)


# ================= LOOP =================

print("🚀 BOT EXTREMOS ACTIVO")

while True:
    try:
        df = get_candles()
        if df is None:
            continue

        support, resistance = get_zones(df)
        c = df.iloc[-1]

        if near_close() and can_trade():

            # 🔻 PRECIO ARRIBA → BUSCAR SELL
            if c['high'] >= resistance - ZONE_TOL and rejection_sell(c):
                send("📍 SEÑAL SELL (RESISTENCIA)")
                trade("put")

            # 🔺 PRECIO ABAJO → BUSCAR BUY
            elif c['low'] <= support + ZONE_TOL and rejection_buy(c):
                send("📍 SEÑAL BUY (SOPORTE)")
                trade("call")

        time.sleep(0.2)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
