import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# VARIABLES
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["GBPUSD-OTC", "EURGBP-OTC", "GBPJPY-OTC", "USDZAR-OTC", "EURJPY-OTC"]

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 1000

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

last_candle_time = 0
bot_running = True

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

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper'] = ma + 2*std
    df['lower'] = ma - 2*std

    return df

# ================= SEÑALES =================

def check_buy(df):
    if len(df) < 6:
        return False

    prev = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    return (
        c3['close'] < c3['ema_100'] and
        c3['close'] <= c3['lower'] and
        c3['close'] < c3['open'] and
        (c3['upper'] > c3['ema_100'] and prev['upper'] <= prev['ema_100']) and
        c4['close'] > c4['open'] and
        c5['close'] > c5['open']
    )


def check_sell(df):
    if len(df) < 6:
        return False

    prev = df.iloc[-5]
    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]

    return (
        c3['close'] > c3['ema_100'] and
        c3['close'] >= c3['upper'] and
        c3['close'] > c3['open'] and
        (c3['lower'] < c3['ema_100'] and prev['lower'] >= prev['ema_100']) and
        c4['close'] < c4['open'] and
        c5['close'] < c5['open']
    )

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 20:
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
            send_telegram(f"{pair} {direction.upper()} ejecutada")
        else:
            send_telegram(f"{pair} error ejecución")

    except:
        send_telegram(f"{pair} fallo trade")

# ================= INICIO =================

send_telegram("🤖 BOT ACTIVO")

# ================= LOOP =================

while True:
    try:
        now = int(time.time())

        if now % 60 != 0 or now == last_candle_time:
            time.sleep(0.5)
            continue

        last_candle_time = now

        print("Analizando nueva vela...")

        for pair in PAIRS:
            df = get_candles(pair)

            if df is None:
                continue

            df = calculate_indicators(df)

            if check_buy(df):
                trade("call", pair)

            elif check_sell(df):
                trade("put", pair)

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        send_telegram("⚠️ Error recuperado")
        time.sleep(3)
