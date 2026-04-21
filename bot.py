import time
import os
import requests
import pandas as pd
import threading
from datetime import datetime, UTC
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

# ================= SESIÓN =================

def is_trading_time():
    # puedes dejarlo siempre activo o limitar horario
    return True

# ================= PROTECCIÓN =================

def safe_thread_exception(args):
    if "underlying" in str(args.exc_value):
        return
    print("Thread error:", args)

threading.excepthook = safe_thread_exception

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

# evitar error digital
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

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        print("Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

def get_candles():
    try:
        candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 50:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except:
        return None

def apply_config():
    config = PAIR_CONFIG.get(PAIR)

    if not config:
        print("❌ No hay configuración para EURUSD-OTC")
        return False

    estrategia.MIN_BODY = config["MIN_BODY"]
    estrategia.MIN_WIDTH = config["MIN_WIDTH"]
    estrategia.TOL = config["TOL"]

    return True

def can_trade():
    global last_trade_time
    now = time.time()

    if now - last_trade_time < COOLDOWN:
        return False

    last_trade_time = now
    return True

def wait_open():
    # esperar apertura exacta de vela
    while True:
        if iq.get_server_timestamp() % 60 == 0:
            return
        time.sleep(0.05)

def trade(direction):
    try:
        status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

        if status:
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

# ================= LOOP =================

while True:
    try:
        reconnect()

        # mantener contenedor vivo
        print(".", end="", flush=True)

        if not is_trading_time():
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        # detectar cierre de vela
        if current_candle == last_candle_time:
            time.sleep(0.2)
            continue

        print("\nNueva vela cerrada")
        last_candle_time = current_candle

        if not apply_config():
            time.sleep(1)
            continue

        df = get_candles()

        if df is None:
            continue

        df = calculate_indicators(df)

        buy = check_buy_signal(df)
        sell = check_sell_signal(df)

        print(f"EURUSD-OTC -> BUY:{buy} SELL:{sell}")

        if buy and can_trade():
            print("Esperando apertura...")
            wait_open()
            trade("call")

        elif sell and can_trade():
            print("Esperando apertura...")
            wait_open()
            trade("put")

        time.sleep(0.2)

    except Exception as e:
        print("\nError:", e)
        time.sleep(3)
