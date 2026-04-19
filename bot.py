import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= VARIABLES =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC"]

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10000

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

last_candle_time = None

# ================= TELEGRAM =================

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= RECONEXIÓN =================

def reconnect():
    try:
        if not iq.check_connect():
            iq.connect()
            iq.change_balance("PRACTICE")
    except:
        pass

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 30:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except:
        return None

# ================= TRADING =================

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"✅ {pair} {direction.upper()} ejecutada"
            print(msg)
            send_telegram(msg)
    except:
        pass

# ================= LOOP =================

send_telegram("🤖 BOT ACTIVO")

while True:
    try:
        reconnect()

        # obtener tiempo del servidor
        server_time = iq.get_server_timestamp()

        # detectar cierre de vela
        current_candle = server_time // 60

        if current_candle == last_candle_time:
            time.sleep(1)
            continue

        # nueva vela cerrada
        last_candle_time = current_candle

        for pair in PAIRS:
            df = get_candles(pair)

            if df is None:
                continue

            # 🔥 eliminar vela en formación
            df = df.iloc[:-1]

            df = calculate_indicators(df)

            # 🔥 analizar SOLO vela cerrada
            if check_buy_signal(df):
                trade("call", pair)

            elif check_sell_signal(df):
                trade("put", pair)

        time.sleep(1)

    except Exception:
        time.sleep(3)
