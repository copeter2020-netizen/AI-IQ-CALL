import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 80, time.time())
    except:
        return None

    if not velas or len(velas) < 35:
        return None

    vela_ruptura = velas[-3]
    vela_confirmacion = velas[-2]

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_ruptura) == 0 or rango(vela_confirmacion) == 0:
        return None

    # 🔥 FUERZA INSTITUCIONAL
    if cuerpo(vela_ruptura) < rango(vela_ruptura) * 0.7:
        return None

    if cuerpo(vela_confirmacion) < rango(vela_confirmacion) * 0.7:
        return None

    # ==========================
    # 🔥 TENDENCIA ULTRA FUERTE
    # ==========================
    estructura = velas[-30:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 18
    tendencia_bajista = bajistas >= 18

    # ==========================
    # 🔥 NIVELES LIMPIOS
    # ==========================
    maximo = max(v["max"] for v in velas[-35:-3])
    minimo = min(v["min"] for v in velas[-35:-3])

    rompe_arriba = vela_ruptura["close"] > maximo
    rompe_abajo = vela_ruptura["close"] < minimo

    # ==========================
    # 🔥 FILTRO FAKE BREAKOUT PRO
    # ==========================
    ruptura_real_alcista = (
        rompe_arriba and
        vela_confirmacion["close"] > vela_ruptura["close"]
    )

    ruptura_real_bajista = (
        rompe_abajo and
        vela_confirmacion["close"] < vela_ruptura["close"]
    )

    # ==========================
    # 🔥 CONFIRMACIÓN INSTITUCIONAL
    # ==========================
    confirmacion_call = (
        vela_confirmacion["close"] > vela_confirmacion["open"] and
        ruptura_real_alcista
    )

    confirmacion_put = (
        vela_confirmacion["close"] < vela_confirmacion["open"] and
        ruptura_real_bajista
    )

    # ==========================
    # 🔥 ANTI LATERAL EXTREMO
    # ==========================
    zona = velas[-25:]
    rango_total = max(v["max"] for v in zona) - min(v["min"] for v in zona)

    if rango_total < rango(vela_ruptura) * 4:
        return None

    # ==========================
    # 🔺 CALL
    # ==========================
    if tendencia_alcista and confirmacion_call:
        return {"action": "call"}

    # ==========================
    # 🔻 PUT
    # ==========================
    if tendencia_bajista and confirmacion_put:
        return {"action": "put"}

    return None
