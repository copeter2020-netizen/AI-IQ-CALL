import time


# ==========================
# 🔥 SOPORTE Y RESISTENCIA 3H
# ==========================
def obtener_niveles(iq, par):

    try:
        velas = iq.get_candles(par, 10800, 50, time.time())
    except:
        return [], []

    soportes = []
    resistencias = []

    for i in range(2, len(velas) - 2):

        # soporte
        if velas[i]["min"] < velas[i-1]["min"] and velas[i]["min"] < velas[i+1]["min"]:
            soportes.append(velas[i]["min"])

        # resistencia
        if velas[i]["max"] > velas[i-1]["max"] and velas[i]["max"] > velas[i+1]["max"]:
            resistencias.append(velas[i]["max"])

    return soportes[-5:], resistencias[-5:]


# ==========================
# 🔥 DETECTAR TRAMPA (FAKE BREAKOUT)
# ==========================
def detectar_trampa(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # 🔥 rompimiento falso arriba → venta
    if c2["max"] > c1["max"] and c1["close"] < c1["open"]:
        return "put"

    # 🔥 rompimiento falso abajo → compra
    if c2["min"] < c1["min"] and c1["close"] > c1["open"]:
        return "call"

    return None


# ==========================
# 🔥 FILTRO CERCA DE ZONA
# ==========================
def cerca_nivel(precio, niveles):
    for n in niveles:
        if abs(precio - n) < 0.0006:
            return True
    return False


# ==========================
# 🔥 CONFIRMACIÓN DE CONTINUIDAD
# ==========================
def confirmacion(candles, señal):

    c1 = candles[-1]

    # vela fuerte (sin indecisión)
    cuerpo = abs(c1["close"] - c1["open"])
    rango = c1["max"] - c1["min"]

    if rango == 0:
        return False

    if cuerpo < rango * 0.6:
        return False

    if señal == "call" and c1["close"] > c1["open"]:
        return True

    if señal == "put" and c1["close"] < c1["open"]:
        return True

    return False


# ==========================
# 🔥 FUNCIÓN PRINCIPAL (IMPORTANTE)
# ==========================
def detectar_trampa(iq, par):
    """
    ESTA ES LA FUNCIÓN QUE TU BOT IMPORTA:
    from strategy import detectar_trampa
    """

    try:
        candles = iq.get_candles(par, 60, 20, time.time())
    except:
        return None

    if not candles:
        return None

    soportes, resistencias = obtener_niveles(iq, par)

    precio = candles[-1]["close"]

    # 🔥 detectar trampa
    señal = detectar_trampa_basica(candles)

    if not señal:
        return None

    # 🔥 FILTRO INSTITUCIONAL (ZONAS)
    if señal == "call" and not cerca_nivel(precio, soportes):
        return None

    if señal == "put" and not cerca_nivel(precio, resistencias):
        return None

    # 🔥 CONFIRMACIÓN FINAL
    if not confirmacion(candles, señal):
        return None

    return {
        "action": señal,
        "precio": precio,
        "soportes": soportes,
        "resistencias": resistencias
    }


# 🔥 ESTA FUNCIÓN ES INTERNA (NO LA IMPORTA EL BOT)
def detectar_trampa_basica(candles):

    if len(candles) < 3:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    # fake breakout arriba
    if c2["max"] > c1["max"] and c1["close"] < c1["open"]:
        return "put"

    # fake breakout abajo
    if c2["min"] < c1["min"] and c1["close"] > c1["open"]:
        return "call"

    return None
