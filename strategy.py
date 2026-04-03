import time
import pandas as pd


def calcular_bollinger(close, period=20):

    ma = close.rolling(period).mean()
    std = close.rolling(period).std()

    upper = ma + (std * 2)
    lower = ma - (std * 2)

    return upper, lower


def calcular_sar(high, low, step=0.02, max_step=0.2):

    sar = low.copy()
    trend_up = True
    ep = high.iloc[0]
    af = step

    for i in range(1, len(high)):

        prev_sar = sar.iloc[i - 1]

        if trend_up:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)

            if low.iloc[i] < sar.iloc[i]:
                trend_up = False
                sar.iloc[i] = ep
                ep = low.iloc[i]
                af = step
            else:
                if high.iloc[i] > ep:
                    ep = high.iloc[i]
                    af = min(af + step, max_step)

        else:
            sar.iloc[i] = prev_sar + af * (ep - prev_sar)

            if high.iloc[i] > sar.iloc[i]:
                trend_up = True
                sar.iloc[i] = ep
                ep = high.iloc[i]
                af = step
            else:
                if low.iloc[i] < ep:
                    ep = low.iloc[i]
                    af = min(af + step, max_step)

    return sar


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 5, 60, time.time())
    except:
        return None

    if not velas or len(velas) < 30:
        return None

    df = pd.DataFrame(velas)
    df = df.sort_values(by="from").reset_index(drop=True)

    close = df["close"].astype(float)
    high = df["max"].astype(float)
    low = df["min"].astype(float)
    open_ = df["open"].astype(float)

    upper, lower = calcular_bollinger(close)
    sar = calcular_sar(high, low)

    if upper.isna().iloc[-1] or lower.isna().iloc[-1]:
        return None

    last = -1
    prev = -2

    precio = close.iloc[last]
    apertura = open_.iloc[last]

    vela_prev_cierre = close.iloc[prev]
    vela_prev_apertura = open_.iloc[prev]

    # 🔻 PUT
    if (
        sar.iloc[last] > precio and
        lower.iloc[last] < precio < upper.iloc[last] and
        vela_prev_cierre > vela_prev_apertura and
        precio > apertura
    ):
        return "put"

    # 🔺 CALL
    if (
        sar.iloc[last] < precio and
        lower.iloc[last] < precio < upper.iloc[last] and
        vela_prev_cierre < vela_prev_apertura and
        precio < apertura
    ):
        return "call"

    return None
