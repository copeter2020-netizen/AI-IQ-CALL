import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 50, time.time())
    except:
        return None

    if not velas or len(velas) < 20:
        return None

    vela_actual = velas[-1]
    vela_anterior = velas[-2]

    # ==========================
    # 🔥 FUNCIONES
    # ==========================
    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    # ==========================
    # 🔥 FILTRO VELA FUERTE
    # ==========================
    if rango(vela_anterior) == 0:
        return None

    fuerza = cuerpo(vela_anterior) / rango(vela_anterior)

    if fuerza < 0.6:
        return None

    # ==========================
    # 🔥 TENDENCIA
    # ==========================
    ultimas = velas[-10:]

    alcistas = sum(1 for v in ultimas if v["close"] > v["open"])
    bajistas = sum(1 for v in ultimas if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 6
    tendencia_bajista = bajistas >= 6

    # ==========================
    # 🔥 SOPORTE / RESISTENCIA
    # ==========================
    maximo = max(v["max"] for v in velas[-15:])
    minimo = min(v["min"] for v in velas[-15:])

    cerca_resistencia = vela_anterior["close"] >= maximo * 0.999
    cerca_soporte = vela_anterior["close"] <= minimo * 1.001

    # ==========================
    # 🚀 CONTINUIDAD (FUERTE)
    # ==========================
    if tendencia_alcista and vela_anterior["close"] > vela_anterior["open"]:
        return {"action": "call"}

    if tendencia_bajista and vela_anterior["close"] < vela_anterior["open"]:
        return {"action": "put"}

    # ==========================
    # 🔄 REVERSIÓN (PRECISA)
    # ==========================
    if cerca_resistencia and vela_anterior["close"] < vela_anterior["open"]:
        return {"action": "put"}

    if cerca_soporte and vela_anterior["close"] > vela_anterior["open"]:
        return {"action": "call"}

    return None
