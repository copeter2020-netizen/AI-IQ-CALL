import time


# =========================
# 🔥 ESTRUCTURA SIMPLE 3H
# =========================
def estructura_3h(iq, par):

    try:
        velas = iq.get_candles(par, 10800, 30, time.time())
    except:
        return None

    if not velas:
        return None

    maximo = max(c["max"] for c in velas)
    minimo = min(c["min"] for c in velas)

    return minimo, maximo


# =========================
# 🔥 ENTRADA M1 (MENOS ESTRICTA)
# =========================
def entrada_m1(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # 🟢 COMPRA
    if (
        c2["close"] < c2["open"] and
        c1["close"] > c1["open"]
    ):
        return "call"

    # 🔴 VENTA
    if (
        c2["close"] > c2["open"] and
        c1["close"] < c1["open"]
    ):
        return "put"

    return None


# =========================
# 🔥 FUNCIÓN PRINCIPAL
# =========================
def detectar_trampa(iq, par):

    estructura = estructura_3h(iq, par)

    if not estructura:
        return None

    soporte, resistencia = estructura

    try:
        candles = iq.get_candles(par, 60, 20, time.time())
    except:
        return None

    if not candles:
        return None

    precio = candles[-1]["close"]

    señal = entrada_m1(candles)

    if not señal:
        return None

    # 🔥 FILTRO ZONA (RELAX)
    if señal == "call" and precio < (soporte + 0.0015):
        return {"action": "call"}

    if señal == "put" and precio > (resistencia - 0.0015):
        return {"action": "put"}

    # 🔥 SI NO ESTÁ EN ZONA → IGUAL ENTRA (para que opere)
    return {"action": señal}
