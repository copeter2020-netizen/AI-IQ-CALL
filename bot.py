import time
import os
import requests
import pandas as pd
import threading
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 100

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 🔥 CONTROL DE OPERACIONES
last_candle_time = None
last_trade_time = {}   # evita múltiples entradas por par
COOLDOWN = 120         # segundos (2 minutos)

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

try:
    iq.api.digital_option = None
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


def can_trade(pair):
    now = time.time()
    last = last_trade_time.get(pair, 0)

    # 🔥 evita múltiples entradas
    return (now - last) > COOLDOWN


def trade(direction, pair):
    try:
        if not can_trade(pair):
            return

        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            last_trade_time[pair] = time.time()

            msg = f"✅ {pair} {direction.upper()} M2"
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

        # 🔥 SOLO CUANDO CIERRA UNA VELA
        if current_candle == last_candle_time:
            time.sleep(1)
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

            # 🔥 SOLO SEÑALES NUEVAS
            buy = check_buy_signal(df, pair)
            sell = check_sell_signal(df, pair)

            if buy:
                trade("call", pair)

            elif sell:
                trade("put", pair)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
