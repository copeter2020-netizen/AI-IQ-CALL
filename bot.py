import time
import os
import requests
import pandas as pd
from iqoptionapi.stable_api import IQ_Option
from strategy import calculate_indicators, check_buy_signal, check_sell_signal

# VARIABLES DE ENTORNO (Railway / GitHub)
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 15

bot_running = True

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


iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()
iq.change_balance("PRACTICE")

send_telegram("🤖 Bot iniciado correctamente")


def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 150, time.time())
    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)
    return df


def execute_trade(direction):
    status, _ = iq.buy(AMOUNT, PAIR, direction, EXPIRATION)

    if status:
        send_telegram(f"📊 Operación ejecutada: {direction.upper()} | ${AMOUNT}")
    else:
        send_telegram("❌ Error al ejecutar operación")


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
