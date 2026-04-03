import time
import numpy as np


def calcular_sar(velas, step=0.02, max_step=0.2):

    high = [v["max"] for v in velas]
    low = [v["min"] for v in velas]

    sar = [low[0]]
    ep = high[0]
    af = step
    uptrend = True

    for i in range(1, len(velas)):

        prev = sar[-1]

        if uptrend:
            new = prev + af * (ep - prev)

            if low[i] < new:
                uptrend = False
                new = ep
                ep = low[i]
                af = step
            else:
                if high[i] > ep:
                    ep = high[i]
                    af = min(af + step, max_step)

        else:
            new = prev + af * (ep - prev)

            if high[i] > new:
                uptrend = True
                new = ep
                ep = high[i]
                af = step
            else:
                if low[i] < ep:
                    ep = low[i]
                    af = min(af + step, max_step)

        sar.append(new)

    return sar


def bollinger(velas, period=20):

    closes = [v["close"] for v in velas]

    if len(closes) < period:
        return None, None

    sma = np.mean(closes[-period:])
    std = np.std(closes[-period:])

    return sma + 2 * std, sma - 2 * std


# 🔥 AJUSTE CLAVE → SIEMPRE GENERA ENTRADAS VÁLIDAS
def detectar_entrada(iq, par):

    try:
        velas5 = iq.get_candles(par, 5, 60, time.time())
    except:
        return None

    if len(velas5) < 30:
        return None

    sar = calcular_sar(velas5)
    upper, lower = bollinger(velas5)

    if upper is None:
        return None

    vela = velas5[-2]
    sar_actual = sar[-2]

    # 👉 SAR dentro de bandas
    if not (lower <= sar_actual <= upper):
        return None

    # 👉 DIRECCIÓN
    if sar_actual > vela["close"]:
        return "put"

    if sar_actual < vela["close"]:
        return "call"

    return None
