import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 70, time.time())
    except:
        return None

    if not velas or len(velas) < 25:
        return None

    vela_ruptura = velas[-3]
    vela_confirmacion = velas[-2]

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_ruptura) == 0 or rango(vela_confirmacion) == 0:
        return None

    # 🔥 MENOS ESTRICTO (ANTES 0.7)
    if cuerpo(vela_ruptura) < rango(vela_ruptura) * 0.55:
        return None

    if cuerpo(vela_confirmacion) < rango(vela_confirmacion) * 0.55:
        return None

    # ==========================
    # 🔥 TENDENCIA FLEXIBLE
    # ==========================
    estructura = velas[-20:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    # 🔥 ANTES 18 → AHORA 11
    tendencia_alcista = alcistas >= 11
    tendencia_bajista = bajistas >= 11

    # ==========================
    # 🔥 NIVELES
    # ==========================
    maximo = max(v["max"] for v in velas[-25:-3])
    minimo = min(v["min"] for v in velas[-25:-3])

    rompe_arriba = vela_ruptura["close"] > maximo
    rompe_abajo = vela_ruptura["close"] < minimo

    # ==========================
    # 🔥 CONFIRMACIÓN (SE MANTIENE FUERTE)
    # ==========================
    confirmacion_call = (
        vela_confirmacion["close"] > vela_confirmacion["open"] and
        vela_confirmacion["close"] > vela_ruptura["close"]
    )

    confirmacion_put = (
        vela_confirmacion["close"] < vela_confirmacion["open"] and
        vela_confirmacion["close"] < vela_ruptura["close"]
    )

    # ==========================
    # 🔥 ANTI LATERAL (MENOS ESTRICTO)
    # ==========================
    zona = velas[-15:]
    rango_total = max(v["max"] for v in zona) - min(v["min"] for v in zona)

    # 🔥 ANTES *4 → AHORA *2.5
    if rango_total < rango(vela_ruptura) * 2.5:
        return None

    # ==========================
    # 🔺 CALL
    # ==========================
    if tendencia_alcista and rompe_arriba and confirmacion_call:
        return {"action": "call"}

    # ==========================
    # 🔻 PUT
    # ==========================
    if tendencia_bajista and rompe_abajo and confirmacion_put:
        return {"action": "put"}

    return None
