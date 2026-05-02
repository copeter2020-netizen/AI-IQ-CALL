import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import check_signal

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 2700

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

bot_active = True
last_update_id = None

# 🔥 CONTROL
last_trade_candle = None
last_signal_candle = None
last_pair = None

# ================= TELEGRAM =================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT LIMPIO (SCORE 10)")
send("🔥 BOT LIMPIO (SCORE 10)")

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()
    df["ema200"] = df["close"].ewm(span=200).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    df["range"] = df["high"] - df["low"]
    df["avg_range"] = df["range"].rolling(10).mean()

    return df

# ================= SCORE =================

def calculate_score(df, signal):
    score = 0
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if signal == "call" and last["ema20"] > last["ema50"] > last["ema200"]:
        score += 3
    elif signal == "put" and last["ema20"] < last["ema50"] < last["ema200"]:
        score += 3

    if signal == "call" and last["rsi"] < 30 and prev["rsi"] < 35:
        score += 2
    elif signal == "put" and last["rsi"] > 70 and prev["rsi"] > 65:
        score += 2

    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]

    if candle_range > 0 and (body / candle_range) > 0.7:
        score += 2

    if signal == "call" and last["close"] > prev["high"]:
        score += 2
    elif signal == "put" and last["close"] < prev["low"]:
        score += 2

    if last["range"] > last["avg_range"]:
        score += 1

    return score

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)

        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        df = add_indicators(df)

        return df
    except:
        return None

# ================= TRADE =================

def trade(pair, direction, score):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} | score {score}"
            print(msg)
            send(msg)

    except:
        pass

# ================= LOOP =================

while True:
    try:
        server_time = int(iq.get_server_timestamp())
        current_candle = server_time // 60

        # 🔥 evitar múltiples señales en misma vela
        if last_signal_candle == current_candle:
            time.sleep(1)
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 50:
                continue

            signal, base_score = check_signal(df)

            if not signal:
                continue

            score = base_score + calculate_score(df, signal)

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        # 🔥 SOLO SCORE 10 Y SIN REPETIR PAR
        if best_pair and best_score >= 10 and best_pair != last_pair:

            trade(best_pair, best_signal, best_score)

            last_trade_candle = current_candle
            last_signal_candle = current_candle
            last_pair = best_pair

        else:
            print(f"…filtrado (score {best_score})")

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
