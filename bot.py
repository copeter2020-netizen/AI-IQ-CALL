import time
import os
import pandas as pd
import requests

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal
from ai_auto import load, predict, save_trade, auto_retrain

# CONFIG
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = 1
EXPIRATION = 1

DAILY_STOP = -10   # 💥 límite diario
MAX_LOSS_STREAK = 3

profit = 0
loss_streak = 0

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                      data={"chat_id": CHAT, "text": msg})
    except:
        pass

def connect():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()
    iq.change_balance("PRACTICE")
    return iq

iq = connect()
model = load()

def get_pairs():
    data = iq.get_all_open_time()
    return [p for p in data["binary"] if "OTC" in p and data["binary"][p]["open"]]

def get_df(pair):
    candles = iq.get_candles(pair, 60, 120, time.time())
    df = pd.DataFrame(candles)
    df.rename(columns={"max":"high","min":"low"}, inplace=True)
    return df

def wait_open():
    while iq.get_server_timestamp() % 60 != 0:
        time.sleep(0.01)

def trade(pair, direction):
    global profit, loss_streak, model

    status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

    if not status:
        return

    time.sleep(65)  # esperar resultado

    result = iq.check_win_v4(_)

    win = 1 if result > 0 else 0

    profit += result

    if win:
        loss_streak = 0
    else:
        loss_streak += 1

    save_trade(df, win)
    model = auto_retrain(model)

    send(f"{pair} {direction} → {'WIN' if win else 'LOSS'} | Profit: {profit}")

while True:
    try:
        if profit <= DAILY_STOP or loss_streak >= MAX_LOSS_STREAK:
            send("🛑 STOP alcanzado")
            break

        pairs = get_pairs()

        best = None

        for pair in pairs:
            df = get_df(pair)
            df = calculate_indicators(df)

            signal = check_signal(df)
            if not signal:
                continue

            prob = predict(model, df)

            if prob > 0.65:
                best = (pair, signal, prob)

        if best:
            pair, signal, prob = best
            send(f"📡 {pair} {signal} prob={prob:.2f}")

            wait_open()
            trade(pair, signal)

        time.sleep(1)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
