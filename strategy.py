import time
import numpy as np


# =========================
# 🔥 INDICADORES
# =========================

def SMA(data, period=20):
    if len(data) < period:
        return None
    return np.mean(data[-period:])


def calcular_stochastic(candles, period=14):

    if len(candles) < period:
        return None, None

    highs = [c["max"] for c in candles[-period:]]
    lows = [c["min"] for c in candles[-period:]]
    close = candles[-1]["close"]

    highest = max(highs)
    lowest = min(lows)

    if highest - lowest == 0:
        return None, None

    k = ((close - lowest) / (highest - lowest)) * 100

    return k, k  # simplificado (K = D)


def calcular_sar(candles):

    # 🔥 Simulación simple de dirección SAR
    if len(candles) < 2:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    if c1["close"] > c2["close"]:
        return "alcista"
    else:
        return "bajista"


# =========================
# 🔥 NIVELES (3H)
# =========================

def obtener_niveles(iq, par):

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


# =========================
# 🔥 TRAMPA (PRICE ACTION)
# =========================

def detectar_trampa_basica(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # 🔴 falso rompimiento arriba → venta
    if c2["max"] > c1["max"] and c1["close"] < c1["open"]:
        return "put"

    # 🟢 falso rompimiento abajo → compra
    if c2["min"] < c1["min"] and c1["close"] > c1["open"]:
        return "call"

    return None


def cerca_nivel(precio, niveles):
    for n in niveles:
        if abs(precio - n) < 0.0006:
            return True
    return False


# =========================
# 🔥 CONFIRMACIONES (IMAGEN)
# =========================

def confirmaciones_indicadores(candles, señal):

    closes = [c["close"] for c in candles]

    # SMA
    sma = SMA(closes, 20)
    if not sma:
        return False

    precio = closes[-1]

    # Stochastic
    k, d = calcular_stochastic(candles)
    if k is None:
        return False

    # SAR
    sar = calcular_sar(candles)
    if not sar:
        return False

    # =========================
    # 🟢 CONDICIONES COMPRA
    # =========================
    if señal == "call":

        if precio < sma:
            return False

        if k < 20:
            return False

        if sar != "alcista":
            return False

        return True

    # =========================
    # 🔴 CONDICIONES VENTA
    # =========================
    if señal == "put":

        if precio > sma:
            return False

        if k > 80:
            return False

        if sar != "bajista":
            return False

        return True

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

    soportes, resistencias = obtener_niveles(iq, par)

    precio = candles[-1]["close"]

    señal = detectar_trampa_basica(candles)

    if not señal:
        return None

    # 🔥 FILTRO NIVEL
    if señal == "call" and not cerca_nivel(precio, soportes):
        return None

    if señal == "put" and not cerca_nivel(precio, resistencias):
        return None

    # 🔥 CONFIRMACIONES INDICADORES
    if not confirmaciones_indicadores(candles, señal):
        return None

    return {
        "action": señal
    }
