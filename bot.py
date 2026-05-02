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
AMOUNT = 500

PAIRS = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "AUDCAD-OTC"
]

last_candle = 0
pending = None
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

print("🔥 BOT ACTIVO (INVERTIDO)")
send("🔥 BOT ACTIVO (INVERTIDO)")

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# ================= SCORE (ADAPTADO A INVERSIÓN) =================

def calculate_score(df, signal):
    score = 0
    last = df.iloc[-1]

    # 🔥 OJO: lógica invertida
    if signal == "call" and last["ema20"] < last["ema50"]:
        score += 2
    elif signal == "put" and last["ema20"] > last["ema50"]:
        score += 2

    # RSI invertido
    if signal == "call" and last["rsi"] > 70:
        score += 2
    elif signal == "put" and last["rsi"] < 30:
        score += 2

    # fuerza de vela
    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]

    if candle_range > 0 and (body / candle_range) > 0.6:
        score += 1

    return score

# ================= INVERTIR SEÑAL =================

def invert_signal(signal):
    if signal == "call":
        return "put"
    elif signal == "put":
        return "call"
    return None

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

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 {pair} {direction.upper()} ${AMOUNT}"
            print(msg)
            send(msg)

    except:
        pass

# ================= ESPERA =================

def wait_open():
    while True:
        if int(iq.get_server_timestamp()) % 60 == 0:
            time.sleep(0.05)
            return
        time.sleep(0.002)

# ================= LOOP =================

while True:
    try:
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        server_time = iq.get_server_timestamp()
        current_candle = server_time // 60

        if current_candle == last_candle:
            time.sleep(0.1)
            continue

        last_candle = current_candle

        # ejecutar entrada pendiente
        if pending:
            wait_open()
            trade(pending[0], pending[1])
            pending = None
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        # analizar pares
        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 50:
                continue

            signal, base_score = check_signal(df)

            if not signal:
                continue

            # 🔥 invertir aquí
            inverted = invert_signal(signal)

            score = base_score + calculate_score(df, inverted)

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = inverted

        # filtro
        if best_pair and best_score >= 4:

            pending = (best_pair, best_signal)

            msg = f"📡 {best_pair} {best_signal.upper()} | score {best_score}"
            print(msg)
            send(msg)

        else:
            print("…sin señal")

    except Exception as e:
        print("Error loop:", e)
        time.sleep(1)
