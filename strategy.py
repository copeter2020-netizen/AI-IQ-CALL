import time
import numpy as np


# =========================
# 🔥 NIVELES 3 HORAS
# =========================
def obtener_estructura(iq, par):

    try:
        velas = iq.get_candles(par, 10800, 60, time.time())  # 3H
    except:
        return None

    if not velas:
        return None

    highs = [c["max"] for c in velas]
    lows = [c["min"] for c in velas]

    resistencia = max(highs[-20:])
    soporte = min(lows[-20:])

    tendencia = "rango"

    if velas[-1]["close"] > np.mean(highs[-20:]):
        tendencia = "alcista"
    elif velas[-1]["close"] < np.mean(lows[-20:]):
        tendencia = "bajista"

    return soporte, resistencia, tendencia


# =========================
# 🔥 CONFIRMACIÓN M1
# =========================
def confirmacion_entrada(candles, accion):

    c1 = candles[-1]
    c2 = candles[-2]

    # vela fuerte confirmación
    cuerpo = abs(c1["close"] - c1["open"])
    rango = c1["max"] - c1["min"]

    if rango == 0:
        return False

    fuerza = cuerpo / rango

    if fuerza < 0.6:
        return False

    # confirmación dirección
    if accion == "call":
        return c1["close"] > c1["open"] and c2["close"] < c2["open"]

    if accion == "put":
        return c1["close"] < c1["open"] and c2["close"] > c2["open"]

    return False


# =========================
# 🔥 FUNCIÓN PRINCIPAL
# =========================
def detectar_trampa(iq, par):

    # 🔥 ESTRUCTURA 3H
    estructura = obtener_estructura(iq, par)

    if not estructura:
        return None

    soporte, resistencia, tendencia = estructura

    # 🔥 M1
    try:
        candles = iq.get_candles(par, 60, 30, time.time())
    except:
        return None

    if not candles:
        return None

    precio = candles[-1]["close"]

    # =========================
    # 🟢 COMPRA (rebote soporte)
    # =========================
    if abs(precio - soporte) < 0.0007:

        if confirmacion_entrada(candles, "call"):
            return {"action": "call"}

    # =========================
    # 🔴 VENTA (rebote resistencia)
    # =========================
    if abs(precio - resistencia) < 0.0007:

        if confirmacion_entrada(candles, "put"):
            return {"action": "put"}

    return None
