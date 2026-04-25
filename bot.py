import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

PAIRS = ["EURUSD", "EURJPY", "GBPUSD", "USDCHF", "EURGBP"]

TIMEFRAME = 60          # velas de 1 minuto
EXPIRATION = 4          # expiración 4 minutos
AMOUNT = 1              # 1 dólar

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
    except Exception as e:
        print("Telegram error:", e)

# ================= IQ OPTION =================

def connect_iq():
    iq = IQ_Option(EMAIL, PASSWORD)

    print("🔌 Conectando...")
    iq.connect()

    if not iq.check_connect():
        print("❌ Error de conexión")
        send_telegram("❌ Error conectando a IQ Option")
        return None

    iq.change_balance("PRACTICE")
    print("✅ Conectado")
    send_telegram("✅ Bot conectado a IQ Option")

    return iq

iq = connect_iq()

# ================= FUNCIONES =================

def reconnect():
    global iq
    if iq is None or not iq.check_connect():
        print("♻️ Reconectando...")
        iq = connect_iq()

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 120, time.time())

        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)

        return df

    except Exception as e:
        print(f"Error obteniendo velas {pair}:", e)
        return None

def is_asset_open(pair):
    try:
        assets = iq.get_all_open_time()
        return assets["binary"][pair]["open"]
    except:
        return False

def trade(pair, direction):
    try:
        if not is_asset_open(pair):
            print(f"⛔ {pair} cerrado")
            return

        status, trade_id = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} EJECUTADO ($1)"
            print(msg)
            send_telegram(msg)
        else:
            print(f"❌ Falló trade {pair}")
            send_telegram(f"❌ Falló trade {pair}")

    except Exception as e:
        print("Error en trade:", e)

# ================= INICIO =================

print("🔥 BOT TII NEXT CANDLE ACTIVO ($1)")
send_telegram("🔥 BOT TII NEXT CANDLE ACTIVO ($1)")

# ================= LOOP =================

while True:
    try:
        reconnect()

        if iq is None:
            time.sleep(3)
            continue

        # Tiempo del servidor
        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in PAIRS:

            # Ejecutar solo en nueva vela
            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            print(f"\n📊 Nueva vela detectada: {pair}")

            # ================= EJECUTAR SEÑAL =================
            if pair in pending_signal:
                direction = pending_signal[pair]

                print(f"🚀 Ejecutando {pair} {direction}")
                trade(pair, direction)

                del pending_signal[pair]
                continue

            # ================= ANALIZAR =================
            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            if signal:
                pending_signal[pair] = signal

                msg = f"📡 {pair} {signal.upper()} DETECTADO → ENTRADA SIGUIENTE VELA"
                print(msg)
                send_telegram(msg)

        time.sleep(0.5)

    except Exception as e:
        print("🔥 ERROR GENERAL:", e)
        time.sleep(2)
