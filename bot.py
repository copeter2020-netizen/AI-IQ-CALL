import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC"]

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10000

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

# 🔥 memoria para no repetir trades
last_signal_time = {}

def send_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 30:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except:
        return None

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            send_telegram(f"✅ {pair} {direction.upper()} ejecutada")
        else:
            send_telegram(f"❌ {pair} error ejecución")

    except:
        send_telegram(f"⚠️ {pair} fallo trade")

send_telegram("🤖 BOT ACTIVO")

while True:
    try:
        # 🔥 esperar cierre real de vela (más seguro que %60)
        time.sleep(2)

        for pair in PAIRS:
            df = get_candles(pair)

            if df is None:
                continue

            # 🔥 eliminar vela en formación
            df = df.iloc[:-1]

            df = calculate_indicators(df)

            # 🔥 revisar últimas 3 velas cerradas
            for i in range(1, 4):
                sub_df = df.iloc[:-(i-1)] if i > 1 else df

                candle_time = sub_df.index[-1]

                # evitar repetir señal
                if pair in last_signal_time and last_signal_time[pair] == candle_time:
                    continue

                if check_buy_signal(sub_df):
                    trade("call", pair)
                    last_signal_time[pair] = candle_time
                    print(f"{pair} BUY detectado en vela {-i}")
                    break

                elif check_sell_signal(sub_df):
                    trade("put", pair)
                    last_signal_time[pair] = candle_time
                    print(f"{pair} SELL detectado en vela {-i}")
                    break

        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        send_telegram("⚠️ Error recuperado")
        time.sleep(3)
