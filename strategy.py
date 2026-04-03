import time
import pandas as pd
import ta


def detectar_entrada(iq, par):

    velas = iq.get_candles(par, 5, 60, time.time())
    df = pd.DataFrame(velas)

    close = df["close"]
    high = df["max"]
    low = df["min"]
    open_ = df["open"]

    # INDICADORES DEFAULT
    bb = ta.volatility.BollingerBands(close)
    upper = bb.bollinger_hband()
    lower = bb.bollinger_lband()

    sar = ta.trend.PSARIndicator(high, low, close).psar()

    last = -1
    prev = -2

    precio = close.iloc[last]
    apertura = open_.iloc[last]

    # 🔻 PUT
    if sar.iloc[last] > precio and lower.iloc[last] < precio < upper.iloc[last]:

        if close.iloc[prev] > open_.iloc[prev]:  # vela verde

            if precio > apertura:
                return "put"

    # 🔺 CALL
    if sar.iloc[last] < precio and lower.iloc[last] < precio < upper.iloc[last]:

        if close.iloc[prev] < open_.iloc[prev]:  # vela roja

            if precio < apertura:
                return "call"

    return None
