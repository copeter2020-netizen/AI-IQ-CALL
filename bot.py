import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option

# VARIABLES
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10

bot_running = True
last_update_id = None

# ================= TELEGRAM =================

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message}, timeout=5)
    except:
        pass


def check_telegram_commands():
    global bot_running, last_update_id
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        params = {"timeout": 5, "offset": last_update_id}
        response = requests.get(url, params=params, timeout=5).json()

        if "result" in response:
            for update in response["result"]:
                last_update_id = update["update_id"] + 1

                if "message" in update:
                    text = update["message"].get("text", "")

                    if text == "/stop":
                        bot_running = False
                        send_telegram("🛑 Bot en pausa")

                    elif text == "/start":
                        bot_running = True
                        send_telegram("✅ Bot activo")

    except:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)

def ensure_connection():
    while True:
        try:
            if not iq.check_connect():
                iq.connect()

            if iq.check_connect():
                iq.change_balance("PRACTICE")
                return True
        except:
            pass

        send_telegram("🔄 Reconectando a IQ Option...")
        time.sleep(5)

ensure_connection()
send_telegram("🤖 Bot online y analizando")

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    df['ma'] = df['close'].rolling(window=14).mean()
    df['std'] = df['close'].rolling(window=14).std()

    df['upper_band'] = df['ma'] + (df['std'] * 2)
    df['lower_band'] = df['ma'] - (df['std'] * 2)

    return df

# ================= SEÑALES =================

def check_buy_signal(df):
    if len(df) < 6:
        return False

    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    return (
        c3['close'] < c3['ema_100'] and
        c3['close'] <= c3['lower_band'] * 1.01 and
        c3['close'] < c3['open'] and
        (c4['upper_band'] > c4['ema_100'] and c3['upper_band'] <= c3['ema_100']) and
        c5['close'] > c5['open'] and
        c6['close'] > c6['open']
    )


def check_sell_signal(df):
    if len(df) < 6:
        return False

    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    return (
        c3['close'] > c3['ema_100'] and
        c3['close'] >= c3['upper_band'] * 0.99 and
        c3['close'] > c3['open'] and
        (c4['lower_band'] < c4['ema_100'] and c3['lower_band'] >= c3['ema_100']) and
        c5['close'] < c5['open'] and
        c6['close'] < c6['open']
    )

# ================= DATOS =================

def get_candles():
    try:
        candles = iq.get_candles(PAIR, TIMEFRAME, 100, time.time())

        if not candles or len(candles) < 20:
            return None

        df = pd.DataFrame(candles)
        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except:
        return None

# ================= TRADING =================

def execute_trade(direction):
    try:
        status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

        if status:
            send_telegram(f"📊 {direction.upper()} ejecutada")
        else:
            send_telegram("❌ Error al ejecutar trade")

    except:
        send_telegram("❌ Fallo en ejecución")

# ================= LOOP PRINCIPAL =================

while True:
    try:
        check_telegram_commands()

        if not iq.check_connect():
            ensure_connection()

        if not bot_running:
            time.sleep(1)
            continue

        df = get_candles()

        if df is None:
            time.sleep(2)
            continue

        df = calculate_indicators(df)

        if check_buy_signal(df):
            execute_trade("call")
            time.sleep(120)
            continue

        if check_sell_signal(df):
            execute_trade("put")
            time.sleep(120)
            continue

        # 🔥 Esto asegura que SIEMPRE esté analizando
        print("Analizando mercado...")
        time.sleep(1)

    except Exception as e:
        print("ERROR:", e)
        send_telegram("⚠️ Error recuperado, bot sigue activo")
        time.sleep(3)
