import time
import os
import requests
import pandas as pd
import threading
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option

import estrategia
from estrategia import calculate_indicators, check_buy_signal, check_sell_signal
from config import PAIR_CONFIG

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 10000

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle_time = None
last_trade_time = 0
COOLDOWN = 60

def is_trading_time():
    hour = datetime.utcnow().hour
    return 7 <= hour <= 20

def safe_thread_exception(args):
    if "underlying" in str(args.exc_value):
        return
    print("Thread error:", args)

threading.excepthook = safe_thread_exception

iq = IQ_Option(EMAIL, PASSWORD)

try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

def reconnect():
    if not iq.check_connect():
        iq.connect()
        iq.change_balance("PRACTICE")

def get_pairs():
    try:
        open_time = iq.get_all_open_time()
        return [
            p for p in open_time["binary"].keys()
            if p.endswith("-OTC") and p in PAIR_CONFIG
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

def apply_pair_config(pair):
    config = PAIR_CONFIG.get(pair)

    if not config:
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
    while True:
        if iq.get_server_timestamp() % 60 == 0:
            return
        time.sleep(0.05)

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🎯 {pair} {direction.upper()}"
            print(msg)
            send_telegram(msg)

    except Exception as e:
        print("Trade error:", e)

send_telegram("🤖 BOT OPTIMIZADO ACTIVO")

while True:
    try:
        reconnect()

        if not is_trading_time():
            time.sleep(10)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle_time:
            time.sleep(0.3)
            continue

        last_candle_time = current_candle

        for pair in get_pairs():

            if not apply_pair_config(pair):
                continue

            df = get_candles(pair)

            if df is None:
                continue

            df = calculate_indicators(df)

            buy = check_buy_signal(df)
            sell = check_sell_signal(df)

            if buy and can_trade():
                wait_open()
                trade("call", pair)

            elif sell and can_trade():
                wait_open()
                trade("put", pair)

        time.sleep(0.3)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
