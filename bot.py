import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

LOOKBACK = 50
ZONE_TOL = 0.0004
MIN_TOUCHES = 2  # 🔥 mínimo 2 o 3 toques

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


# ================= DETECCIÓN DE ZONAS FUERTES =================

def find_strong_zones(df):
    recent = df.iloc[-LOOKBACK:]

    supports = []
    resistances = []

    for i in range(2, len(recent) - 2):
        low = recent['low'].iloc[i]
        high = recent['high'].iloc[i]

        # detectar pivote bajo
        if low < recent['low'].iloc[i-1] and low < recent['low'].iloc[i+1]:
            supports.append(low)

        # detectar pivote alto
        if high > recent['high'].iloc[i-1] and high > recent['high'].iloc[i+1]:
            resistances.append(high)

    # agrupar zonas repetidas
    def cluster_levels(levels):
        zones = []
        for level in levels:
            added = False
            for z in zones:
                if abs(level - z['price']) <= ZONE_TOL:
                    z['count'] += 1
                    added = True
                    break
            if not added:
                zones.append({'price': level, 'count': 1})
        return zones

    support_zones = cluster_levels(supports)
    resistance_zones = cluster_levels(resistances)

    # filtrar zonas fuertes
    strong_supports = [z['price'] for z in support_zones if z['count'] >= MIN_TOUCHES]
    strong_resistances = [z['price'] for z in resistance_zones if z['count'] >= MIN_TOUCHES]

    return strong_supports, strong_resistances


# ================= RECHAZO =================

def strong_rejection_buy(c):
    body = abs(c['close'] - c['open'])
    wick = min(c['open'], c['close']) - c['low']
    return wick > body * 1.2


def strong_rejection_sell(c):
    body = abs(c['close'] - c['open'])
    wick = c['high'] - max(c['open'], c['close'])
    return wick > body * 1.2


# ================= TIEMPO =================

def near_close():
    server_time = iq.get_server_timestamp()
    return server_time % 60 >= 55


# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN


# ================= TRADE =================

def trade(direction):
    global last_trade_time

    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        last_trade_time = time.time()
        msg = f"🎯 TRADE {direction.upper()} (ZONA FUERTE)"
        print(msg)
        send(msg)


# ================= LOOP =================

print("🚀 BOT ZONAS FUERTES ACTIVO")

while True:
    try:
        df = get_candles()
        if df is None:
            continue

        supports, resistances = find_strong_zones(df)
        c = df.iloc[-1]

        if near_close() and can_trade():

            # 🟢 SOPORTES
            for s in supports:
                if c['low'] <= s + ZONE_TOL:
                    if strong_rejection_buy(c):
                        send("📍 SOPORTE FUERTE → CALL")
                        trade("call")
                        break

            # 🔴 RESISTENCIAS
            for r in resistances:
                if c['high'] >= r - ZONE_TOL:
                    if strong_rejection_sell(c):
                        send("📍 RESISTENCIA FUERTE → PUT")
                        trade("put")
                        break

        time.sleep(0.2)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
