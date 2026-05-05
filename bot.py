import time
import os
import requests
import pandas as pd
import sys
import logging

from iqoptionapi.stable_api import IQ_Option
from estrategia import add_indicators, pro_signal

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

AMOUNT = 2000

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC"
]

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
last_trade_candle = -1
bot_active = True
last_update_id = None
current_expiration = 1

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

print("🔥 BOT SNIPER PRO ACTIVO")
send("🔥 BOT SNIPER PRO ACTIVO")

# ================= DATOS =================

def get_candles(pair, tf):
    try:
        data = iq.get_candles(pair, tf, 100, time.time())
        df = pd.DataFrame(data)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return add_indicators(df)
    except:
        return None

# ================= FILTRO VOLATILIDAD =================

def is_market_dead(df):
    atr = df["atr"].iloc[-1]
    atr_mean = df["atr"].mean()

    return atr < atr_mean * 0.5

# ================= ESPERA =================

def wait_candle_almost_close():
    while True:
        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        t = int(iq.get_server_timestamp())

        if t % 60 >= 58:
            return

        time.sleep(0.05)

# ================= TRADE =================

def trade(pair, direction, expiration):
    global trade_open, last_trade_time, current_expiration

    try:
        status, _ = iq.buy(AMOUNT, pair, direction, expiration)

        if status:
            trade_open = True
            last_trade_time = time.time()
            current_expiration = expiration

            msg = f"🎯 {pair} {direction.upper()} ({expiration}m)"
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

        # esperar cierre de operación
        if trade_open:
            wait_time = current_expiration * 60 + 5
            if time.time() - last_trade_time > wait_time:
                trade_open = False
            else:
                time.sleep(1)
                continue

        wait_candle_almost_close()

        server_time = int(iq.get_server_timestamp())
        current_candle = server_time // 60

        if last_trade_candle == current_candle:
            continue

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            if df_m1 is None or df_m5 is None:
                continue

            if is_market_dead(df_m1):
                continue

            signal, expiration = pro_signal(df_m1, df_m5)

            if signal:
                trade(pair, signal, expiration)
                last_trade_candle = current_candle
                break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)
