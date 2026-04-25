import time
import os
import requests
import pandas as pd
import threading

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = {}
pending_signal = {}

# ================= FIX THREAD ERROR =================

def ignore_thread_error(args):
    if "underlying" in str(args.exc_value):
        return
    print("Thread error:", args)

threading.excepthook = ignore_thread_error

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

def connect_iq():
    iq = IQ_Option(EMAIL, PASSWORD)

    print("🔌 Conectando...")
    iq.connect()

    if not iq.check_connect():
        print("❌ Error conexión")
        return None

    iq.change_balance("PRACTICE")
    print("✅ Conectado")

    return iq

iq = connect_iq()

# ================= FIX UNDERLYING =================

def safe_get_underlying():
    try:
        data = iq.get_digital_underlying_list_data()
        if not data or "underlying" not in data:
            return {"underlying": []}
        return data
    except:
        return {"underlying": []}

if iq:
    iq.get_digital_underlying_list_data = safe_get_underlying

# ================= FUNCIONES =================

def reconnect():
    global iq
    if iq is None or not iq.check_connect():
        print("♻️ Reconectando...")
        iq = connect_iq()

        if iq:
            iq.get_digital_underlying_list_data = safe_get_underlying

def get_all_otc_pairs():
    try:
        data = iq.get_all_open_time()
        pairs = []

        for pair in data["binary"]:
            if "OTC" in pair and data["binary"][pair]["open"]:
                pairs.append(pair)

        return pairs

    except:
        return []

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

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} EJECUTADO ($1)"
            print(msg)
            send_telegram(msg)
        else:
            print(f"❌ Falló trade {pair}")

    except Exception as e:
        print("Trade error:", e)

# ================= INICIO =================

print("🔥 BOT OTC 1M ACTIVO")
send_telegram("🔥 BOT OTC 1M ACTIVO")

# ================= LOOP =================

while True:
    try:
        reconnect()

        if iq is None:
            time.sleep(3)
            continue

        pairs = get_all_otc_pairs()

        if not pairs:
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in pairs:

            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            # 🔥 EJECUTAR
            if pair in pending_signal:
                direction = pending_signal[pair]
                trade(pair, direction)
                del pending_signal[pair]
                continue

            # 🔍 ANALIZAR
            df = get_candles(pair)
            if df is None or len(df) < 50:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            if signal:
                pending_signal[pair] = signal
                send_telegram(f"📡 {pair} {signal.upper()} → SIGUIENTE VELA")

        time.sleep(0.5)

    except Exception as e:
        print("Error general:", e)
        time.sleep(2)
