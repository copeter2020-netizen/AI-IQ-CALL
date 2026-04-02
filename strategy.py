import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 50, time.time())
    except:
        return None

    if not velas or len(velas) < 20:
        return None

    vela_estructura = velas[-3]
    vela_confirmacion = velas[-2]

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_estructura) == 0 or rango(vela_confirmacion) == 0:
        return None

    # 🔥 fuerza de vela (evita doji)
    if cuerpo(vela_estructura) < rango(vela_estructura) * 0.5:
        return None

    if cuerpo(vela_confirmacion) < rango(vela_confirmacion) * 0.5:
        return None

    # 🔥 tendencia
    estructura = velas[-15:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 9
    tendencia_bajista = bajistas >= 9

    # 🔥 ruptura de estructura
    maximo = max(v["max"] for v in velas[-20:-3])
    minimo = min(v["min"] for v in velas[-20:-3])

    rompe_arriba = vela_estructura["close"] > maximo
    rompe_abajo = vela_estructura["close"] < minimo

    # 🔥 confirmación
    confirmacion_alcista = vela_confirmacion["close"] > vela_confirmacion["open"]
    confirmacion_bajista = vela_confirmacion["close"] < vela_confirmacion["open"]

    # 🔺 CALL
    if tendencia_alcista and rompe_arriba and confirmacion_alcista:
        return {"action": "call"}

    # 🔻 PUT
    if tendencia_bajista and rompe_abajo and confirmacion_bajista:
        return {"action": "put"}

    return None
