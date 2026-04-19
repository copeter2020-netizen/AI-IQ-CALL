import time
from iqoptionapi.stable_api import IQ_Option
from strategy import calculate_indicators, check_buy_signal, check_sell_signal
import pandas as pd

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

iq.change_balance("PRACTICE")

PAIR = "EURUSD-OTC"
TIMEFRAME = 60
EXPIRATION = 2
AMOUNT = 10


def get_candles():
    candles = iq.get_candles(PAIR, TIMEFRAME, 150, time.time())
    df = pd.DataFrame(candles)
    df.rename(columns={"max": "high", "min": "low"}, inplace=True)
    return df


def execute_trade(direction):
    iq.buy(AMOUNT, PAIR, direction, EXPIRATION)


while True:
    try:
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
        print(e)
        time.sleep(5)
