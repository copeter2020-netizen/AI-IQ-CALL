import time


# =========================
# 🔥 ESTRUCTURA 3H
# =========================
def estructura(iq, par):

    try:
        velas = iq.get_candles(par, 10800, 20, time.time())
    except:
        return None

    if not velas:
        return None

    maximo = max(c["max"] for c in velas)
    minimo = min(c["min"] for c in velas)

    return minimo, maximo


# =========================
# 🔥 ENTRADA M1
# =========================
def entrada(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # COMPRA
    if c2["close"] < c2["open"] and c1["close"] > c1["open"]:
        return "call"

    # VENTA
    if c2["close"] > c2["open"] and c1["close"] < c1["open"]:
        return "put"

    return None


# =========================
# 🔥 MAIN
# =========================
def detectar_trampa(iq, par):

    zona = estructura(iq, par)

    if not zona:
        return None

    soporte, resistencia = zona

    try:
        candles = iq.get_candles(par, 60, 20, time.time())
    except:
        return None

    if not candles:
        return None

    señal = entrada(candles)

    if not señal:
        return None

    precio = candles[-1]["close"]

    # 🔥 filtro suave (para que SI opere)
    if señal == "call" and precio < soporte + 0.002:
        return {"action": "call"}

    if señal == "put" and precio > resistencia - 0.002:
        return {"action": "put"}

    # 🔥 fallback (SIEMPRE OPERA)
    return {"action": señal}
