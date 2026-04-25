import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

TIMEFRAME = 60
EXPIRATION = 5  # 🔥 1 MINUTO
AMOUNT = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = {}
pending_signal = {}

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

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        print("Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

def get_all_otc_pairs():
    """Obtiene TODOS los pares OTC abiertos"""
    try:
        all_assets = iq.get_all_open_time()
        pairs = []

        for market in all_assets:
            for pair in all_assets[market]:
                if "OTC" in pair and all_assets[market][pair]["open"]:
                    pairs.append(pair)

        return pairs

    except Exception as e:
        print("Error obteniendo pares:", e)
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

print("🔥 BOT OTC SCANNER 1M ACTIVO")
send_telegram("🔥 BOT OTC SCANNER 1M ACTIVO")

# ================= LOOP =================

while True:
    try:
        reconnect()

        pairs = get_all_otc_pairs()

        if not pairs:
            print("No hay pares OTC abiertos")
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in pairs:

            # evitar repetir vela
            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            # 🔥 EJECUTAR SI HAY SEÑAL PENDIENTE
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
                msg = f"📡 {pair} {signal.upper()} PREPARADO (SIGUIENTE VELA)"
                print(msg)
                send_telegram(msg)

        time.sleep(0.5)

    except Exception as e:
        print("Error general:", e)
        time.sleep(2)
