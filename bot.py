import time
import os
import pandas as pd
from datetime import datetime

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal
from ai_auto import predict

# ================= CONFIG =================

AMOUNT = 1
TIMEFRAME = 60
EXPIRATION = 1

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

# ================= CONEXIÓN =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if iq.check_connect():
    print("✅ Conectado a IQ Option")
else:
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        print("🔄 Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

def get_all_pairs():
    try:
        assets = iq.get_all_open_time()
        pairs = []

        for pair, data in assets["digital"].items():
            if data["open"] and "OTC" in pair:
                pairs.append(pair)

        return pairs

    except Exception as e:
        print("Error obteniendo pares:", e)
        return []

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())

        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)

        return df

    except Exception as e:
        print(f"Error velas {pair}:", e)
        return None

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            print(f"🔥 TRADE EJECUTADO → {pair} {direction}")
        else:
            print(f"❌ Falló trade → {pair}")

    except Exception as e:
        print("Error trade:", e)

# ================= INICIO =================

print("🔥 BOT SCANNER IA ACTIVO (OTC 1M)")

last_candle = {}

# ================= LOOP =================

while True:
    try:
        reconnect()

        pairs = get_all_pairs()

        if not pairs:
            print("⚠️ No hay pares disponibles")
            time.sleep(2)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in pairs:

            # evitar repetir misma vela
            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            # IA decide si entrar
            if signal and predict():

                print(f"📊 Señal detectada → {pair} {signal}")

                trade(pair, signal)

                # 🔥 SOLO UNA ENTRADA POR CICLO
                break

        time.sleep(1)

    except Exception as e:
        print("Error general:", e)
        time.sleep(2)
