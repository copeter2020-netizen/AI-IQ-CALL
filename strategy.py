import time
import numpy as np


# ==========================
# SAR
# ==========================
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


# ==========================
# BOLLINGER
# ==========================
def bollinger(velas, period=20):

    closes = [v["close"] for v in velas]

    if len(closes) < period:
        return None, None

    sma = np.mean(closes[-period:])
    std = np.std(closes[-period:])

    upper = sma + (2 * std)
    lower = sma - (2 * std)

    return upper, lower


# ==========================
# 🔥 LÓGICA EXACTA TUYA
# ==========================
def detectar_entrada(iq, par):

    try:
        velas5 = iq.get_candles(par, 5, 60, time.time())
    except:
        return None

    if not velas5 or len(velas5) < 30:
        return None

    sar = calcular_sar(velas5)
    upper, lower = bollinger(velas5)

    if upper is None:
        return None

    # 👉 PRIMERA BURBUJA
    vela_burbuja = velas5[-5]
    sar_burbuja = sar[-5]

    # 👉 VALIDAR DENTRO DE BANDAS
    if not (lower <= sar_burbuja <= upper):
        return None

    # ==========================
    # DATOS 1 MINUTO
    # ==========================
    try:
        velas1m = iq.get_candles(par, 60, 4, time.time())
    except:
        return None

    vela_confirmacion = velas1m[-3]
    vela_entrada = velas1m[-2]

    apertura = vela_confirmacion["open"]
    cierre = vela_confirmacion["close"]

    # ==========================
    # 🔻 PUT
    # ==========================
    if sar_burbuja > vela_burbuja["close"]:

        # vela termina CALL
        if cierre > apertura:

            # precio actual mayor apertura
            if vela_entrada["close"] > vela_entrada["open"]:
                return "put"

    # ==========================
    # 🔺 CALL
    # ==========================
    if sar_burbuja < vela_burbuja["close"]:

        # vela termina PUT
        if cierre < apertura:

            if vela_entrada["close"] < vela_entrada["open"]:
                return "call"

    return None
