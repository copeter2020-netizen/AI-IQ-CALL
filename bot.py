import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal

# ================= CONFIG =================

PAIRS = ["EURUSD", "EURJPY", "GBPUSD", "USDCHF", "EURGBP"]

TIMEFRAME = 60
EXPIRATION = 4
AMOUNT = 1  # ✅ 1 DÓLAR

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = {}
pending_signal = {}  # 🔥 guarda señal para siguiente vela

# ================= HORARIO =================

def is_trading_time():
    now = datetime.now(timezone.utc)
    bogota_hour = (now.hour - 5) % 24
    return 7 <= bogota_hour < 10  # overlap

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

# FIX ERROR UNDERLYING
try:
    iq.api.digital_option = None
    iq.get_digital_underlying_list_data = lambda: {"underlying": []}
except:
    pass

iq.connect()
iq.change_balance("PRACTICE")

# ================= FUNCIONES =================

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

print("🔥 BOT TII NEXT CANDLE ACTIVO ($1)")
send_telegram("🔥 BOT TII NEXT CANDLE ACTIVO ($1)")

# ================= LOOP =================

while True:
    try:
        reconnect()

        if not is_trading_time():
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        for pair in PAIRS:

            # detectar nueva vela
            if pair in last_candle and last_candle[pair] == current_candle:
                continue

            last_candle[pair] = current_candle

            # 🔥 SI HAY SEÑAL PENDIENTE → EJECUTA
            if pair in pending_signal:
                direction = pending_signal[pair]
                trade(pair, direction)
                del pending_signal[pair]
                continue

            # 🔍 ANALIZAR NUEVA SEÑAL
            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)
            signal = check_signal(df)

            if signal:
                pending_signal[pair] = signal
                send_telegram(f"📡 {pair} {signal.upper()} PREPARADO (SIGUIENTE VELA)")

        time.sleep(0.2)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
