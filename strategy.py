import time
import numpy as np


# =========================
# 🔥 INDICADORES
# =========================

def SMA(data, period=20):
    if len(data) < period:
        return None
    return np.mean(data[-period:])


def stochastic(candles, period=14):

    if len(candles) < period:
        return None

    highs = [c["max"] for c in candles[-period:]]
    lows = [c["min"] for c in candles[-period:]]
    close = candles[-1]["close"]

    highest = max(highs)
    lowest = min(lows)

    if highest - lowest == 0:
        return None

    k = ((close - lowest) / (highest - lowest)) * 100
    return k


def sar_direccion(candles):

    if len(candles) < 2:
        return None

    if candles[-1]["close"] > candles[-2]["close"]:
        return "alcista"
    else:
        return "bajista"


# =========================
# 🔥 SOPORTE Y RESISTENCIA (3H)
# =========================

def niveles(iq, par):

    try:
        velas = iq.get_candles(par, 10800, 50, time.time())
    except:
        return [], []

    soportes = []
    resistencias = []

    for i in range(2, len(velas) - 2):

        if velas[i]["min"] < velas[i-1]["min"] and velas[i]["min"] < velas[i+1]["min"]:
            soportes.append(velas[i]["min"])

        if velas[i]["max"] > velas[i-1]["max"] and velas[i]["max"] > velas[i+1]["max"]:
            resistencias.append(velas[i]["max"])

    return soportes[-5:], resistencias[-5:]


def cerca(precio, niveles):
    for n in niveles:
        if abs(precio - n) < 0.0006:
            return True
    return False


# =========================
# 🔥 TRAMPA (PRICE ACTION)
# =========================

def detectar_trampa_basica(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # falso rompimiento arriba → venta
    if c2["max"] > c1["max"] and c1["close"] < c1["open"]:
        return "put"

    # falso rompimiento abajo → compra
    if c2["min"] < c1["min"] and c1["close"] > c1["open"]:
        return "call"

    return None


# =========================
# 🔥 CONFIRMACIONES
# =========================

def confirmar(candles, señal):

    closes = [c["close"] for c in candles]
    precio = closes[-1]

    sma = SMA(closes, 20)
    k = stochastic(candles)
    sar = sar_direccion(candles)

    if sma is None or k is None or sar is None:
        return False

    if señal == "call":
        return precio > sma and k > 20 and sar == "alcista"

    if señal == "put":
        return precio < sma and k < 80 and sar == "bajista"

    return False


# =========================
# 🔥 FUNCIÓN PRINCIPAL
# =========================

def detectar_trampa(iq, par):

    try:
        candles = iq.get_candles(par, 60, 30, time.time())
    except:
        return None

    if not candles:
        return None

    soportes, resistencias = niveles(iq, par)

    precio = candles[-1]["close"]

    señal = detectar_trampa_basica(candles)

    if not señal:
        return None

    if señal == "call" and not cerca(precio, soportes):
        return None

    if señal == "put" and not cerca(precio, resistencias):
        return None

    if not confirmar(candles, señal):
        return None

    return {"action": señal}
