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
EXPIRATION = 1
AMOUNT = 2500

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


def check_commands():
    global bot_active, last_update_id

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 1, "offset": last_update_id}

        r = requests.get(url, params=params, timeout=5).json()

        for result in r.get("result", []):
            last_update_id = result["update_id"] + 1

            if "message" not in result:
                continue

            text = result["message"].get("text", "")

            if text == "/stop":
                bot_active = False
                send("⛔ BOT DETENIDO")

            elif text == "/start":
                bot_active = True
                send("✅ BOT ACTIVADO")

    except:
        pass

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT ACTIVO (ENTRADA INMEDIATA)")
send("🔥 BOT ACTIVO (ENTRADA INMEDIATA)")

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # rango promedio (detectar lateral)
    df["range"] = df["high"] - df["low"]
    df["avg_range"] = df["range"].rolling(10).mean()

    return df

# ================= FILTRO PRO =================

def calculate_score(df, signal):
    score = 0
    last = df.iloc[-1]

    # tendencia fuerte
    if signal == "call" and last["ema20"] > last["ema50"]:
        score += 2
    elif signal == "put" and last["ema20"] < last["ema50"]:
        score += 2

    # RSI extremo
    if signal == "call" and last["rsi"] < 30:
        score += 2
    elif signal == "put" and last["rsi"] > 70:
        score += 2

    # vela fuerte
    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]

    if candle_range > 0 and (body / candle_range) > 0.65:
        score += 2

    # evitar lateral (clave)
    if last["range"] > last["avg_range"]:
        score += 1

    return score

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)

        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

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
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        # analizar TODO en tiempo real
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

        # 🔥 ENTRADA INMEDIATA (SIN ESPERAR)
        if best_pair and best_score >= 5:

            trade(best_pair, best_signal, best_score)

            # pequeña pausa para no sobreoperar
            time.sleep(10)

        else:
            print("…sin señal")

        time.sleep(1)

    except Exception as e:
        print("Error loop:", e)
        time.sleep(1)
