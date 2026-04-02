import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 50, time.time())
    except:
        return None

    if not velas or len(velas) < 20:
        return None

    # ==========================
    # 🔥 VELAS CLAVE
    # ==========================
    vela_1 = velas[-3]  # estructura
    vela_2 = velas[-2]  # confirmación

    # ==========================
    # 🔧 FUNCIONES
    # ==========================
    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_1) == 0 or rango(vela_2) == 0:
        return None

    # ==========================
    # 🔥 FILTRO FUERZA (NO DOJI)
    # ==========================
    if cuerpo(vela_1) < rango(vela_1) * 0.5:
        return None

    if cuerpo(vela_2) < rango(vela_2) * 0.5:
        return None

    # ==========================
    # 🔥 ESTRUCTURA DEL MERCADO
    # ==========================
    estructura = velas[-15:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 9
    tendencia_bajista = bajistas >= 9

    # ==========================
    # 🔥 RUPTURA DE ESTRUCTURA
    # ==========================
    maximo = max(v["max"] for v in velas[-20:-3])
    minimo = min(v["min"] for v in velas[-20:-3])

    rompe_arriba = vela_1["close"] > maximo
    rompe_abajo = vela_1["close"] < minimo

    # ==========================
    # 🔥 CONTINUIDAD (CONFIRMACIÓN)
    # ==========================
    continuidad_alcista = vela_2["close"] > vela_2["open"]
    continuidad_bajista = vela_2["close"] < vela_2["open"]

    # ==========================
    # 🔺 COMPRA (CALL)
    # ==========================
    if (
        tendencia_alcista and
        rompe_arriba and
        continuidad_alcista
    ):
        return {"action": "call"}

    # ==========================
    # 🔻 VENTA (PUT)
    # ==========================
    if (
        tendencia_bajista and
        rompe_abajo and
        continuidad_bajista
    ):
        return {"action": "put"}

    return None
