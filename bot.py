import time
import os
import requests
import pandas as pd
import threading
from datetime import datetime, timezone
from iqoptionapi.stable_api import IQ_Option

import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal
from config import PAIR_CONFIG

# ================= CONFIG =================

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle_time = None
last_trade_time = 0
COOLDOWN = 60

# ================= THREAD SAFE =================

def safe_thread_exception(args):
    if "underlying" in str(args.exc_value):
        return
    print("Thread error:", args)

threading.excepthook = safe_thread_exception

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

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
    if not iq.check_connect():
        print("🔄 Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

# ================= CANDLES =================

def get_candles():
    try:
        candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 50:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)

        df = df.sort_values("from")
        df.reset_index(drop=True, inplace=True)

        return df

    except:
        return None

# ================= CONFIG PAIR =================

def apply_config():
    config = PAIR_CONFIG.get(PAIR)

    if not config:
        print("❌ No hay configuración para EURUSD-OTC")
        return False

    estrategia.MIN_BODY = config["MIN_BODY"]
    estrategia.MIN_WIDTH = config["MIN_WIDTH"]
    estrategia.TOL = config["TOL"]

    return True

# ================= FILTRO DE MERCADO =================

def market_filter(df):
    last_range = df["high"].iloc[-1] - df["low"].iloc[-1]
    avg_range = (df["high"] - df["low"]).mean()

    return last_range >= avg_range * 0.6

# ================= CONTROL DE TRADING =================

def can_trade():
    return (time.time() - last_trade_time) >= COOLDOWN

def wait_open():
    while True:
        if iq.get_server_timestamp() % 60 < 1:
            time.sleep(0.5)
            return
        time.sleep(0.1)

def trade(direction):
    global last_trade_time

    try:
        status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

        if status:
            last_trade_time = time.time()
            msg = f"🎯 {PAIR} {direction.upper()}"
            print(msg)
            send_telegram(msg)
        else:
            print("❌ Falló ejecución")

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

print("🤖 BOT EURUSD-OTC ACTIVO")
send_telegram("🤖 BOT EURUSD-OTC ACTIVO")

if not apply_config():
    exit()

# ================= LOOP PRINCIPAL =================

while True:
    try:
        reconnect()
        print(".", end="", flush=True)

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        # esperar nueva vela
        if current_candle == last_candle_time:
            time.sleep(0.2)
            continue

        last_candle_time = current_candle
        print("\n📊 Nueva vela cerrada")

        df = get_candles()
        if df is None:
            continue

        df = calculate_indicators(df)

        if not market_filter(df):
            continue

        buy = check_buy_signal(df)
        sell = check_sell_signal(df)

        print(f"EURUSD-OTC -> BUY:{buy} SELL:{sell}")

        if buy and sell:
            continue

        if buy and can_trade():
            print("⏳ Esperando apertura...")
            wait_open()
            trade("call")

        elif sell and can_trade():
            print("⏳ Esperando apertura...")
            wait_open()
            trade("put")

        time.sleep(0.2)

    except Exception as e:
        print("\nError:", e)
        time.sleep(3)
