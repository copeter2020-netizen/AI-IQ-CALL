import time


# 🔥 SOPORTE / RESISTENCIA (3H)
def niveles_estructura(iq, par):

    velas = iq.get_candles(par, 10800, 50, time.time())

    soportes = []
    resistencias = []

    for i in range(2, len(velas)-2):

        if velas[i]["min"] < velas[i-1]["min"] and velas[i]["min"] < velas[i+1]["min"]:
            soportes.append(velas[i]["min"])

        if velas[i]["max"] > velas[i-1]["max"] and velas[i]["max"] > velas[i+1]["max"]:
            resistencias.append(velas[i]["max"])

    return soportes[-5:], resistencias[-5:]


# 🔥 DETECTAR REVERSIÓN REAL
def detectar_reversion(candles):

    c1 = candles[-1]
    c2 = candles[-2]

    cuerpo = abs(c1["close"] - c1["open"])
    rango = c1["max"] - c1["min"]

    # 🔥 vela fuerte (sin indecisión)
    if cuerpo < rango * 0.6:
        return None

    # 🔥 reversión clara
    if c2["close"] < c2["open"] and c1["close"] > c1["open"]:
        return "call"

    if c2["close"] > c2["open"] and c1["close"] < c1["open"]:
        return "put"

    return None


# 🔥 FILTRO CERCA DE ZONA
def cerca_nivel(precio, niveles):
    for n in niveles:
        if abs(precio - n) < 0.0006:
            return True
    return False


# 🔥 CONTINUIDAD DESPUÉS DE REVERSIÓN
def analizar_entrada(iq, par):

    candles = iq.get_candles(par, 60, 20, time.time())

    if not candles:
        return None

    soportes, resistencias = niveles_estructura(iq, par)

    precio = candles[-1]["close"]

    señal = detectar_reversion(candles)

    if not señal:
        return None

    # 🔥 SOLO EN ZONAS FUERTES
    if señal == "call" and not cerca_nivel(precio, soportes):
        return None

    if señal == "put" and not cerca_nivel(precio, resistencias):
        return None

    # 🔥 CONFIRMACIÓN: VELA ACTUAL CONTINÚA
    c1 = candles[-1]

    if señal == "call" and c1["close"] <= c1["open"]:
        return None

    if señal == "put" and c1["close"] >= c1["open"]:
        return None

    return {
        "action": señal,
        "soportes": soportes,
        "resistencias": resistencias
        }
