import time
import os
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from iqoptionapi.stable_api import IQ_Option
import threading

from estrategia import get_signal

# ================= CONFIG =================

PAIRS = ["EURUSD", "GBPUSD", "EURJPY", "USDCHF", "EURGBP"]

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 100
COOLDOWN = 60

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ================= PROTECCIÓN GLOBAL =================

def ignore_thread_errors(args):
    if "underlying" in str(args.exc_value):
        return  # 🔥 ignorar error de IQ API
    print("Thread error:", args)

threading.excepthook = ignore_thread_errors

# ================= ESTADO =================

last_trade_time = 0
last_candle_time = None

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

# ================= HORA =================

def get_hour():
    utc = datetime.now(timezone.utc)
    bogota = utc - timedelta(hours=5)
    return bogota.hour

def is_trading_time():
    return 8 <= get_hour() < 11

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)

def connect():
    while True:
        try:
            iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")

                # 🔥 DESACTIVAR DIGITAL OPTIONS (CLAVE)
                try:
                    iq.api.digital_option = None
                    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
                except:
                    pass

                print("✅ Conectado limpio")
                return

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)

def reconnect():
    if not iq.check_connect():
        print("Reconectando...")
        connect()

# ================= VALIDACIÓN =================

def is_pair_open(pair):
    try:
        open_time = iq.get_all_open_time()
        return open_time["binary"][pair]["open"]
    except:
        return False

# ================= DATA =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

# ================= CONTROL =================

def can_trade():
    return (time.time() - last_trade_time) > COOLDOWN

# ================= TRADE =================

def trade(pair, direction):
    global last_trade_time

    if not is_pair_open(pair):
        return

    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            last_trade_time = time.time()
            msg = f"🎯 {pair} {direction.upper()}"
            print(msg)
            send(msg)

    except Exception as e:
        print("Trade error:", e)

# ================= LOOP =================

print("🔥 BOT SIN ERROR UNDERLYING")
connect()
send("🔥 BOT ESTABLE ACTIVADO")

while True:
    try:
        reconnect()

        if not is_trading_time():
            time.sleep(60)
            continue

        if not can_trade():
            time.sleep(0.5)
            continue

        server_time = iq.get_server_timestamp()
        candle = server_time // 60

        if candle == last_candle_time:
            time.sleep(0.1)
            continue

        last_candle_time = candle

        for pair in PAIRS:

            if not is_pair_open(pair):
                continue

            df = get_candles(pair)
            if df is None or len(df) < 30:
                continue

            signal = get_signal(df)

            if signal:
                send(f"📊 {pair} {signal.upper()}")

                time.sleep(0.5)
                trade(pair, signal)

                break

    except Exception as e:
        print("ERROR:", e)
        time.sleep(3)
