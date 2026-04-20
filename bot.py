import time
import os
import requests
import pandas as pd
import threading
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle_time = None
last_trade_candle = {}

# ================= PROTECCIÓN =================

def safe_thread_exception(args):
    if "underlying" in str(args.exc_value):
        return
    print("Thread error:", args)

threading.excepthook = safe_thread_exception

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

# evitar errores digitales
try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

VALID_ASSETS = set(iq.get_all_ACTIVES_OPCODE().keys())

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

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        iq.connect()
        iq.change_balance("PRACTICE")


def get_pairs():
    try:
        open_time = iq.get_all_open_time()
        return [
            p for p in open_time["binary"].keys()
            if p.endswith("-OTC") and p in VALID_ASSETS
        ]
    except:
        return []


def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 50:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None


# evitar múltiples entradas en la misma vela
def can_trade(pair, candle_time):
    if last_trade_candle.get(pair) == candle_time:
        return False

    last_trade_candle[pair] = candle_time
    return True


# esperar apertura exacta
def wait_open():
    while True:
        if iq.get_server_timestamp() % 60 == 0:
            return
        time.sleep(0.05)


def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"✅ {pair} {direction.upper()} M1"
            print(msg)
            send_telegram(msg)

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

send_telegram("🤖 BOT ACTIVO")

# ================= LOOP =================

while True:
    try:
        reconnect()

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        # detectar nueva vela cerrada
        if current_candle == last_candle_time:
            time.sleep(0.5)
            continue

        last_candle_time = current_candle

        pairs = get_pairs()

        for pair in pairs:
            df = get_candles(pair)

            if df is None:
                continue

            # eliminar vela en formación
            df = df.iloc[:-1]

            df = calculate_indicators(df)

            buy = check_buy_signal(df, pair)
            sell = check_sell_signal(df, pair)

            if buy and can_trade(pair, current_candle):
                wait_open()
                trade("call", pair)

            elif sell and can_trade(pair, current_candle):
                wait_open()
                trade("put", pair)

        time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
