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
AMOUNT = 100

bot_running = True

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

    cond_trend = c3['close'] < c3['ema_100']
    cond_band = c3['close'] <= c3['lower_band'] * 1.01
    cond_red = c3['close'] < c3['open']

    cross = (c4['upper_band'] > c4['ema_100']) and (c3['upper_band'] <= c3['ema_100'])

    green1 = c5['close'] > c5['open']
    green2 = c6['close'] > c6['open']

    return cond_trend and cond_band and cond_red and cross and green1 and green2


def check_sell_signal(df):
    if len(df) < 6:
        return False

    c3 = df.iloc[-4]
    c4 = df.iloc[-3]
    c5 = df.iloc[-2]
    c6 = df.iloc[-1]

    cond_trend = c3['close'] > c3['ema_100']
    cond_band = c3['close'] >= c3['upper_band'] * 0.99
    cond_green = c3['close'] > c3['open']

    cross = (c4['lower_band'] < c4['ema_100']) and (c3['lower_band'] >= c3['ema_100'])

    red1 = c5['close'] < c5['open']
    red2 = c6['close'] < c6['open']

    return cond_trend and cond_band and cond_green and cross and red1 and red2

# ================= TELEGRAM =================

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        pass


def check_telegram_commands():
    global bot_running
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url).json()

        if "result" in response:
            for update in response["result"][-5:]:
                if "message" in update:
                    text = update["message"].get("text", "")

                    if text == "/stop":
                        bot_running = False
                        send_telegram("🛑 Bot detenido")

                    elif text == "/start":
                        bot_running = True
                        send_telegram("✅ Bot activado")
    except:
        pass

# ================= IQ OPTION =================

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

send_telegram("🤖 Bot iniciado")

# ================= FUNCIONES =================

def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 150, time.time())
    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)
    return df


def execute_trade(direction):
    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        send_telegram(f"📊 {direction.upper()} ejecutada | ${AMOUNT}")
    else:
        send_telegram("❌ Error al ejecutar operación")

# ================= LOOP =================

while True:
    try:
        check_telegram_commands()

        if not bot_running:
            time.sleep(2)
            continue

        df = get_candles()
        df = calculate_indicators(df)

        if check_buy_signal(df):
            execute_trade("call")
            time.sleep(120)

        elif check_sell_signal(df):
            execute_trade("put")
            time.sleep(120)

        time.sleep(1)

    except Exception as e:
        send_telegram(f"⚠️ Error: {str(e)}")
        time.sleep(5)
