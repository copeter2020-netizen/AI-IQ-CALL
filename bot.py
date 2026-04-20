import time
import os
import requests
import pandas as pd
import threading
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= THREAD PROTECTION =================

def safe_thread_exception(args):
    if "underlying" in str(args.exc_value):
        print("⚠️ Error digital ignorado")
        return
    print("Thread error:", args)

threading.excepthook = safe_thread_exception

# ================= VARIABLES =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10000

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

try:
    iq.api.digital_option = None
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

iq.subscribe_strike_list = lambda *args, **kwargs: None
iq.unsubscribe_strike_list = lambda *args, **kwargs: None

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

# ================= PARES ACTIVOS =================

def get_pairs():
    try:
        open_time = iq.get_all_open_time()
        pairs = []

        for pair, data in open_time["binary"].items():
            if isinstance(data, dict) and data.get("open", False):
                pairs.append(pair)

        return pairs

    except:
        return []

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

# ================= TRADE =================

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"✅ {pair} {direction.upper()} M2"
            print(msg)
            send_telegram(msg)
    except:
        pass

# ================= LOOP =================

send_telegram("🤖 BOT ACTIVO")

while True:
    try:
        reconnect()

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle_time:
            time.sleep(1)
            continue

        last_candle_time = current_candle

        pairs = get_pairs()

        for pair in pairs:
            df = get_candles(pair)

            if df is None:
                continue

            # 🔥 CLAVE: trabajar SOLO con velas cerradas
            df = df.iloc[:-1]

            df = calculate_indicators(df)

            # 🔥 ÚNICA LÓGICA
            if check_buy_signal(df):
                trade("call", pair)

            elif check_sell_signal(df):
                trade("put", pair)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
