import time
import os
import requests
import pandas as pd
import threading
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

PAIRS = ["EURUSD", "EURJPY", "GBPUSD", "USDCHF", "EURGBP"]

TIMEFRAME = 60
EXPIRATION = 4
AMOUNT = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = {}
last_trade_time = 0
COOLDOWN = 60

# ================= HORARIO OVERLAP =================

def is_trading_time():
    now = datetime.now(timezone.utc)
    bogota_hour = (now.hour - 5) % 24

    # 7 AM - 10 AM Bogotá
    return 7 <= bogota_hour < 10

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

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)

# FIX ERROR UNDERLYING
try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

# ================= CORE =================

def reconnect():
    if not iq.check_connect():
        iq.connect()
        iq.change_balance("PRACTICE")

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 120, time.time())

        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)

        return df
    except:
        return None

def can_trade():
    global last_trade_time
    now = time.time()

    if now - last_trade_time < COOLDOWN:
        return False

    last_trade_time = now
    return True

def wait_next_candle():
    while True:
        if int(time.time()) % 60 == 0:
            return
        time.sleep(0.05)

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} (4M)"
            print(msg)
            send_telegram(msg)
        else:
            print("❌ Falló trade")

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

print("🔥 BOT TII ACTIVO (OVERLAP)")
send_telegram("🔥 BOT TII ACTIVO (OVERLAP)")

# ================= LOOP =================

while True:
    try:
        reconnect()

        if not is_trading_time():
            time.sleep(5)
            continue

        for pair in PAIRS:

            server_time = iq.get_server_timestamp()
            candle_id = server_time // 60

            if pair in last_candle and last_candle[pair] == candle_id:
                continue

            last_candle[pair] = candle_id

            df = get_candles(pair)

            if df is None:
                continue

            df = calculate_indicators(df)

            signal = check_signal(df)

            if signal and can_trade():
                send_telegram(f"📡 {pair} {signal.upper()} DETECTADO")

                # esperar siguiente vela
                wait_next_candle()

                trade(pair, signal)

        time.sleep(0.2)

    except Exception as e:
        print("Error:", e)
        time.sleep(3)
