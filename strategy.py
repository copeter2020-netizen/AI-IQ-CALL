import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 60, time.time())
    except:
        return None

    if not velas or len(velas) < 30:
        return None

    vela_1 = velas[-3]  # zona
    vela_2 = velas[-2]  # confirmación

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    # evitar errores
    if rango(vela_1) == 0 or rango(vela_2) == 0:
        return None

    # ==========================
    # 🔥 SOPORTE / RESISTENCIA
    # ==========================
    zona = velas[-30:-3]

    resistencia = max(v["max"] for v in zona)
    soporte = min(v["min"] for v in zona)

    margen = (resistencia - soporte) * 0.03

    # ==========================
    # 🔥 TENDENCIA SIMPLE
    # ==========================
    estructura = velas[-15:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 8
    tendencia_bajista = bajistas >= 8

    # ==========================
    # 🔥 CONFIRMACIÓN FUERTE
    # ==========================
    if cuerpo(vela_2) < rango(vela_2) * 0.4:
        return None

    # ==========================
    # 🔥 REVERSIÓN
    # ==========================
    if vela_1["max"] >= (resistencia - margen):

        if vela_2["close"] < vela_2["open"]:
            return {"action": "put"}

    if vela_1["min"] <= (soporte + margen):

        if vela_2["close"] > vela_2["open"]:
            return {"action": "call"}

    # ==========================
    # 🔥 CONTINUIDAD
    # ==========================
    if tendencia_alcista:
        if vela_1["close"] > resistencia:
            if vela_2["close"] > vela_2["open"]:
                return {"action": "call"}

    if tendencia_bajista:
        if vela_1["close"] < soporte:
            if vela_2["close"] < vela_2["open"]:
                return {"action": "put"}

    return None
