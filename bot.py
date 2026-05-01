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

# 🔥 PON TU CHAT_ID MANUAL SI FALLA
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 3500

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
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": msg
        }

        r = requests.post(url, data=data, timeout=5)

        # 🔥 DEBUG
        if r.status_code != 200:
            print("❌ Error Telegram:", r.text)
        else:
            print("✅ Enviado a Telegram")

    except Exception as e:
        print("❌ FALLO TELEGRAM:", e)


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

            chat_id = str(result["message"]["chat"]["id"])

            # 🔥 SOLO TU CHAT
            if chat_id != str(CHAT_ID):
                continue

            text = result["message"].get("text", "")

            if text == "/stop":
                bot_active = False
                send("⛔ BOT DETENIDO")

            elif text == "/start":
                bot_active = True
                send("✅ BOT ACTIVADO")

    except Exception as e:
        print("Error comandos:", e)

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando")
    exit()

iq.change_balance("PRACTICE")
iq.get_digital_underlying_list_data = lambda: {"underlying": []}

print("🔥 BOT ACTIVO")
send("🔥 BOT ACTIVO")

# ================= DATOS =================

def get_candles(pair):
    try:
        candles = iq.get_candles(pair, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)

        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

        return df
    except:
        return None

# ================= TRADE =================

def trade(pair, direction):
    try:
        status, _ = iq.buy(AMOUNT, pair, direction, EXPIRATION)

        if status:
            msg = f"🔥 TRADE: {pair} {direction.upper()} ${AMOUNT}"
            print(msg)
            send(msg)

    except Exception as e:
        print("Error trade:", e)

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

        # ejecutar
        if pending:
            wait_open()
            trade(pending[0], pending[1])
            pending = None
            continue

        best_pair = None
        best_signal = None
        best_score = 0

        for pair in PAIRS:

            df = get_candles(pair)
            if df is None or len(df) < 10:
                continue

            signal, score = check_signal(df)

            if not signal:
                continue

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = signal

        if best_pair and best_score >= 3:

            pending = (best_pair, best_signal)

            msg = f"📡 SEÑAL: {best_pair} {best_signal.upper()} | score {best_score}"
            print(msg)
            send(msg)

        else:
            print("…sin señal")

    except Exception as e:
        print("Error loop:", e)
        time.sleep(1)
