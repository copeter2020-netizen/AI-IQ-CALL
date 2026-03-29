import time


def detectar_zonas(candles):

    soportes = []
    resistencias = []

    for i in range(2, len(candles)-2):

        if (
            candles[i]["min"] < candles[i-1]["min"] and
            candles[i]["min"] < candles[i+1]["min"]
        ):
            soportes.append(candles[i]["min"])

        if (
            candles[i]["max"] > candles[i-1]["max"] and
            candles[i]["max"] > candles[i+1]["max"]
        ):
            resistencias.append(candles[i]["max"])

    return soportes[-5:], resistencias[-5:]


def cerca_nivel(precio, niveles, tolerancia=0.0005):
    for n in niveles:
        if abs(precio - n) <= tolerancia:
            return True
    return False


def vela_rechazo(c):

    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]

    if rango == 0:
        return None

    mecha_sup = c["max"] - max(c["open"], c["close"])
    mecha_inf = min(c["open"], c["close"]) - c["min"]

    # rechazo alcista
    if mecha_inf > cuerpo * 1.5:
        return "call"

    # rechazo bajista
    if mecha_sup > cuerpo * 1.5:
        return "put"

    return None


def analizar_estructura(iq, par):

    # 🔥 MARCO 3 HORAS (velas de 1m = 180 velas)
    velas_macro = iq.get_candles(par, 60, 180, time.time())

    if not velas_macro:
        return None

    soportes, resistencias = detectar_zonas(velas_macro)

    # 🔥 VELAS ACTUALES
    velas = iq.get_candles(par, 60, 5, time.time())

    if not velas:
        return None

    c1 = velas[-1]
    precio = c1["close"]

    rechazo = vela_rechazo(c1)

    # 🔻 SOPORTE → CALL
    if (
        cerca_nivel(precio, soportes) and
        rechazo == "call"
    ):
        return {"action": "call"}

    # 🔺 RESISTENCIA → PUT
    if (
        cerca_nivel(precio, resistencias) and
        rechazo == "put"
    ):
        return {"action": "put"}

    return None
