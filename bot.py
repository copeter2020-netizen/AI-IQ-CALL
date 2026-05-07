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

# 🔥 SOLO EURUSD REAL
PAIR = "EURUSD"

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
current_expiration = 1

bot_active = True
last_update_id = None

# ================= TELEGRAM =================

def send(msg):

    try:

        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=5
        )

    except:
        pass


def check_commands():

    global bot_active
    global last_update_id

    try:

        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={
                "timeout": 1,
                "offset": last_update_id
            },
            timeout=5
        ).json()

        for result in r.get("result", []):

            last_update_id = result["update_id"] + 1

            text = result.get(
                "message",
                {}
            ).get(
                "text",
                ""
            )

            # STOP
            if text == "/stop":

                bot_active = False
                send("⛔ BOT DETENIDO")

            # START
            elif text == "/start":

                bot_active = True
                send("✅ BOT ACTIVADO")

    except:
        pass

# ================= IQ =================

iq = IQ_Option(EMAIL, PASSWORD)

iq.connect()

if not iq.check_connect():

    print("❌ ERROR CONECTANDO")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT EURUSD INSTITUCIONAL ACTIVO")
send("🔥 BOT EURUSD INSTITUCIONAL ACTIVO")

# ================= DATOS =================

def get_candles(pair, tf):

    try:

        candles = iq.get_candles(
            pair,
            tf,
            200,
            time.time()
        )

        df = pd.DataFrame(candles)

        df.rename(
            columns={
                "max": "high",
                "min": "low"
            },
            inplace=True
        )

        return add_indicators(df)

    except:
        return None

# ================= TRADE =================

def trade(pair, direction, expiration):

    global trade_open
    global last_trade_time
    global current_expiration

    try:

        status, _ = iq.buy(
            AMOUNT,
            pair,
            direction,
            expiration
        )

        if status:

            trade_open = True
            last_trade_time = time.time()
            current_expiration = expiration

            msg = (
                f"🎯 {pair} "
                f"{direction.upper()} "
                f"({expiration}m)"
            )

            print(msg)
            send(msg)

    except:
        pass

# ================= LOOP =================

while True:

    try:

        check_commands()

        # bot detenido
        if not bot_active:

            time.sleep(1)
            continue

        # evitar múltiples trades
        if trade_open:

            wait_time = (
                current_expiration * 60
            ) + 5

            if (
                time.time() - last_trade_time
            ) > wait_time:

                trade_open = False

            else:

                time.sleep(1)
                continue

        # ================= TIMING =================

        t = int(iq.get_server_timestamp())

        # últimos segundos vela
        if t % 60 < 57:

            time.sleep(0.2)
            continue

        # ================= DATOS =================

        df_m1 = get_candles(PAIR, 60)
        df_m5 = get_candles(PAIR, 300)

        if df_m1 is None or df_m5 is None:

            time.sleep(1)
            continue

        # ================= SEÑAL =================

        signal, expiration = pro_signal(
            df_m1,
            df_m5
        )

        # ================= TRADE =================

        if signal:

            trade(
                PAIR,
                signal,
                expiration
            )

        time.sleep(1)

    except Exception as e:

        print("Error:", e)
        time.sleep(1)
