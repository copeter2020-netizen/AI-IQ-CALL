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
    "EURUSD"
]

EXPIRATION = 3

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
last_trade_candle = None

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
        response = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates",
            params={
                "timeout": 1,
                "offset": last_update_id
            },
            timeout=5
        ).json()

        for result in response.get("result", []):

            last_update_id = result["update_id"] + 1

            if "message" not in result:
                continue

            text = result["message"].get("text", "").lower()

            # ================= STOP =================

            if text == "/stop":

                bot_active = False

                print("BOT DETENIDO")
                send("⛔ BOT DETENIDO")

            # ================= START =================

            elif text == "/start":

                bot_active = True

                print("BOT ACTIVADO")
                send("✅ BOT ACTIVADO")

    except:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando IQ Option")
    exit()

iq.change_balance("PRACTICE")

print("🔥 BOT IA ACTIVO")
send("🔥 BOT IA ACTIVO")

# ================= CANDLES =================

def get_candles(pair, timeframe):

    try:
        candles = iq.get_candles(
            pair,
            timeframe,
            120,
            time.time()
        )

        df = pd.DataFrame(candles)

        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

        return add_indicators(df)

    except:
        return None

# ================= ESPERAR CIERRE =================

def wait_candle_close():

    while True:

        check_commands()

        if not bot_active:
            time.sleep(1)
            continue

        server_time = int(iq.get_server_timestamp())

        seconds = server_time % 60

        # entra justo al cerrar vela
        if seconds >= 59:
            time.sleep(0.2)
            return

        time.sleep(0.05)

# ================= TRADE =================

def execute_trade(pair, direction):

    global trade_open
    global last_trade_time

    try:

        status, trade_id = iq.buy(
            AMOUNT,
            pair,
            direction,
            EXPIRATION
        )

        if status:

            trade_open = True
            last_trade_time = time.time()

            msg = (
                f"🎯 ENTRADA\n"
                f"PAR: {pair}\n"
                f"DIRECCIÓN: {direction.upper()}\n"
                f"EXPIRACIÓN: {EXPIRATION}m"
            )

            print(msg)
            send(msg)

    except Exception as e:
        print("ERROR TRADE:", e)

# ================= LOOP =================

while True:

    try:

        check_commands()

        # ================= BOT DETENIDO =================

        if not bot_active:
            time.sleep(1)
            continue

        # ================= ESPERA FIN TRADE =================

        if trade_open:

            if time.time() - last_trade_time > (EXPIRATION * 60 + 5):

                trade_open = False

            else:
                time.sleep(1)
                continue

        # ================= ESPERAR CIERRE VELA =================

        wait_candle_close()

        current_candle = int(iq.get_server_timestamp()) // 60

        # evita múltiples entradas misma vela
        if last_trade_candle == current_candle:
            continue

        # ================= ANALISIS =================

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            if df_m1 is None or df_m5 is None:
                continue

            signal = pro_signal(df_m1, df_m5)

            # ================= ENTRADA =================

            if signal:

                execute_trade(pair, signal)

                last_trade_candle = current_candle

                break

        time.sleep(1)

    except Exception as e:

        print("ERROR LOOP:", e)

        time.sleep(2)
