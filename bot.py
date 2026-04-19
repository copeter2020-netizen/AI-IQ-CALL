import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

from estrategia import calculate_indicators, check_buy_signal, check_sell_signal

# ================= VARIABLES =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIRS = ["EURUSD-OTC", "GBPUSD-OTC"]

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 1000

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

# ================= ESTADO =================

last_signal_time = {}
last_heartbeat = time.time()

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
    global iq
    try:
        if not iq.check_connect():
            print("Reconectando...")
            iq.connect()
            iq.change_balance("PRACTICE")
            send_telegram("🔄 Reconectado")
    except:
        print("Error reconexión")

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 30:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except Exception as e:
        print("Error obteniendo velas:", e)
        return None

# ================= TRADING =================

def trade(direction, pair):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"✅ {pair} {direction.upper()} ejecutada"
            print(msg)
            send_telegram(msg)
        else:
            msg = f"❌ {pair} error ejecución"
            print(msg)
            send_telegram(msg)

    except Exception as e:
        print("Error trade:", e)
        send_telegram(f"⚠️ {pair} fallo trade")

# ================= LOOP PRINCIPAL =================

def run_bot():
    global last_signal_time, last_heartbeat

    while True:
        try:
            reconnect()

            time.sleep(2)

            for pair in PAIRS:
                df = get_candles(pair)

                if df is None:
                    continue

                # eliminar vela en formación
                df = df.iloc[:-1]

                df = calculate_indicators(df)

                # revisar últimas 3 velas
                for i in range(1, 4):
                    sub_df = df.iloc[:-(i-1)] if i > 1 else df

                    candle_time = sub_df.index[-1]

                    # evitar repetir señal
                    if pair in last_signal_time and last_signal_time[pair] == candle_time:
                        continue

                    if check_buy_signal(sub_df):
                        print(f"{pair} → BUY detectado en vela {-i}")
                        trade("call", pair)
                        last_signal_time[pair] = candle_time
                        break

                    elif check_sell_signal(sub_df):
                        print(f"{pair} → SELL detectado en vela {-i}")
                        trade("put", pair)
                        last_signal_time[pair] = candle_time
                        break

                print(f"{pair} → analizado")

            # 🔥 heartbeat para Railway
            if time.time() - last_heartbeat > 30:
                print("🤖 Bot activo...")
                last_heartbeat = time.time()

        except Exception as e:
            print("ERROR INTERNO:", e)
            send_telegram("⚠️ Error recuperado")
            time.sleep(5)

# ================= ARRANQUE =================

if __name__ == "__main__":
    send_telegram("🤖 BOT INICIADO")

    while True:
        try:
            run_bot()
        except Exception as e:
            print("REINICIANDO BOT:", e)
            send_telegram("♻️ Reiniciando bot")
            time.sleep(5)
