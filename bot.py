import time
import os
import requests
import pandas as pd
from datetime import datetime, timezone

from iqoptionapi.stable_api import IQ_Option
from estrategia import calculate_indicators, check_signal, score_pair
from ai_auto import allow_trade

# ================= CONFIG =================
TIMEFRAME = 60
EXPIRATION = 1
AMOUNT = 5

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

last_candle = 0

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

# ================= HORARIO (Bogotá) =================
def is_trading_time():
    now = datetime.now(timezone.utc)
    bogota_hour = (now.hour - 5) % 24
    return 7 <= bogota_hour <= 11  # overlap fuerte

# ================= IQ OPTION =================
iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conexión")
    exit()

iq.change_balance("PRACTICE")

# 🔥 evitar error digital
iq.subscribe_strike_list = lambda *args, **kwargs: None
iq.unsubscribe_strike_list = lambda *args, **kwargs: None

print("🏦 BOT HEDGE FUND ACTIVO")
send_telegram("🏦 BOT HEDGE FUND ACTIVO")

# ================= FUNCIONES =================

def reconnect():
    if not iq.check_connect():
        print("🔄 Reconectando...")
        iq.connect()
        iq.change_balance("PRACTICE")

def get_pairs():
    try:
        data = iq.get_all_open_time()
        pairs = []

        for par, info in data.get("binary", {}).items():
            if info.get("open"):
                pairs.append(par)

        return pairs
    except:
        return []

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 200, time.time())
        if not candles:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df
    except:
        return None

def trade(pair, direction, score):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🏦 {pair} {direction.upper()} | SCORE {score}"
            print(msg)
            send_telegram(msg)
        else:
            print(f"❌ Falló trade {pair}")

    except Exception as e:
        print("Trade error:", e)

# ================= LOOP =================

while True:
    try:
        reconnect()

        if not is_trading_time():
            print("⏰ Fuera de horario")
            time.sleep(5)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle:
            time.sleep(0.2)
            continue

        last_candle = current_candle

        pairs = get_pairs()

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in pairs:

            df = get_candles(pair)
            if df is None:
                continue

            df = calculate_indicators(df)

            signal = check_signal(df)
            if not signal:
                continue

            score = score_pair(df)

            # IA decide si vale la pena
            if not allow_trade(score):
                continue

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        if best_pair and best_score >= 3:
            trade(best_pair, best_signal, best_score)
        else:
            print("❌ Sin oportunidad institucional")

        time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
        time.sleep(2)
