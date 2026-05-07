import time
import os
import requests
import pandas as pd
import numpy as np
import sys
import logging

from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================

logging.getLogger().setLevel(logging.CRITICAL)
sys.stderr = open(os.devnull, 'w')

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TIMEFRAME = 60
EXPIRATION = 4

# 🔥 CUENTA REAL - 3 USD
BASE_AMOUNT = 3

MAX_LOSS_STREAK = 3

PAIRS = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "USDCHF-OTC",
    "AUDCAD-OTC"
]

# ================= ESTADO =================

trade_open = False
last_trade_time = 0
last_trade_candle = None

loss_streak = 0
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

# ================= COMANDOS TELEGRAM =================

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

                print("⛔ BOT DETENIDO")
                send("⛔ BOT DETENIDO")

            # ================= START =================

            elif text == "/start":

                bot_active = True

                print("✅ BOT ACTIVADO")
                send("✅ BOT ACTIVADO")

    except:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)

iq.connect()

if not iq.check_connect():

    print("❌ ERROR CONECTANDO")
    exit()

# 🔥 CUENTA REAL
iq.change_balance("REAL")

print("🔥 BOT PRO REAL ACTIVO")
send("🔥 BOT PRO REAL ACTIVO")

# ================= INDICADORES =================

def indicators(df):

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    # ATR
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift()),
            abs(df["low"] - df["close"].shift())
        )
    )

    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ================= DATOS =================

def get_candles(pair, tf):

    try:

        data = iq.get_candles(
            pair,
            tf,
            100,
            time.time()
        )

        df = pd.DataFrame(data)

        df.rename(
            columns={
                "max": "high",
                "min": "low"
            },
            inplace=True
        )

        return indicators(df)

    except:
        return None

# ================= SNIPER PRO =================

def sniper_pro(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]

    # 🔥 tendencia fuerte M5
    trend_up = (
        df_m5.iloc[-1]["ema20"] >
        df_m5.iloc[-1]["ema50"]
    )

    trend_down = (
        df_m5.iloc[-1]["ema20"] <
        df_m5.iloc[-1]["ema50"]
    )

    # 🔥 evitar lateral
    if last["atr"] < df_m1["atr"].mean():
        return None

    body = abs(last["close"] - last["open"])
    candle_range = last["high"] - last["low"]

    if candle_range == 0:
        return None

    strength = body / candle_range

    # ================= PUT =================

    if (

        prev["close"] > prev["open"] and
        last["close"] < last["open"] and

        strength > 0.7 and

        last["close"] < prev["low"] and

        trend_down

    ):

        return "put"

    # ================= CALL =================

    if (

        prev["close"] < prev["open"] and
        last["close"] > last["open"] and

        strength > 0.7 and

        last["close"] > prev["high"] and

        trend_up

    ):

        return "call"

    return None

# ================= TRADE =================

def trade(pair, direction):

    global trade_open
    global last_trade_time

    try:

        status, trade_id = iq.buy(
            BASE_AMOUNT,
            pair,
            direction,
            EXPIRATION
        )

        if status:

            trade_open = True
            last_trade_time = time.time()

            msg = (
                f"🎯 ENTRADA\n\n"
                f"PAR: {pair}\n"
                f"DIRECCIÓN: {direction.upper()}\n"
                f"IMPORTE: ${BASE_AMOUNT}\n"
                f"EXPIRACIÓN: {EXPIRATION}m"
            )

            print(msg)
            send(msg)

    except Exception as e:

        print("ERROR TRADE:", e)

# ================= RESULTADO =================

def check_result():

    global trade_open

    try:

        if not trade_open:
            return

        # esperar resultado
        if time.time() - last_trade_time < 65:
            return

        trade_open = False

    except:

        trade_open = False

# ================= LOOP =================

while True:

    try:

        check_commands()

        # ================= BOT DETENIDO =================

        if not bot_active:

            time.sleep(1)
            continue

        # ================= RESULTADO =================

        check_result()

        # ================= OPERACION ABIERTA =================

        if trade_open:

            time.sleep(1)
            continue

        server_time = int(iq.get_server_timestamp())

        current_candle = server_time // 60

        # evitar múltiples entradas
        if last_trade_candle == current_candle:

            time.sleep(1)
            continue

        # 🔥 entrar últimos segundos
        if server_time % 60 < 57:

            time.sleep(0.2)
            continue

        # ================= ANALISIS =================

        for pair in PAIRS:

            df_m1 = get_candles(pair, 60)
            df_m5 = get_candles(pair, 300)

            if df_m1 is None or df_m5 is None:
                continue

            signal = sniper_pro(df_m1, df_m5)

            if signal:

                # 🔥 protección pérdidas
                if loss_streak >= MAX_LOSS_STREAK:

                    send("🛑 STOP POR RACHAS")

                    time.sleep(120)

                    loss_streak = 0

                    break

                trade(pair, signal)

                last_trade_candle = current_candle

                break

        time.sleep(1)

    except Exception as e:

        print("ERROR LOOP:", e)

        time.sleep(1)
