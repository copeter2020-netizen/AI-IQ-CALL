import time


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 60, 100, time.time())
    except:
        return None

    if not velas or len(velas) < 30:
        return None

    # ==========================
    # 🔥 ÚLTIMAS VELAS
    # ==========================
    vela_zona = velas[-3]
    vela_confirmacion = velas[-2]

    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_zona) == 0 or rango(vela_confirmacion) == 0:
        return None

    # ==========================
    # 🔥 SOPORTE / RESISTENCIA
    # ==========================
    zona = velas[-50:-3]

    resistencia = max(v["max"] for v in zona)
    soporte = min(v["min"] for v in zona)

    # margen de zona (precisión sniper)
    margen = (resistencia - soporte) * 0.02

    toca_resistencia = vela_zona["max"] >= (resistencia - margen)
    toca_soporte = vela_zona["min"] <= (soporte + margen)

    # ==========================
    # 🔥 TENDENCIA
    # ==========================
    estructura = velas[-20:-3]

    alcistas = sum(1 for v in estructura if v["close"] > v["open"])
    bajistas = sum(1 for v in estructura if v["close"] < v["open"])

    tendencia_alcista = alcistas >= 12
    tendencia_bajista = bajistas >= 12

    # ==========================
    # 🔥 FUERZA DE VELAS
    # ==========================
    if cuerpo(vela_zona) < rango(vela_zona) * 0.5:
        return None

    if cuerpo(vela_confirmacion) < rango(vela_confirmacion) * 0.5:
        return None

    # ==========================
    # 🔥 REVERSIÓN (RECHAZO)
    # ==========================
    rechazo_resistencia = (
        toca_resistencia and
        vela_zona["close"] < vela_zona["open"] and
        vela_confirmacion["close"] < vela_confirmacion["open"]
    )

    rechazo_soporte = (
        toca_soporte and
        vela_zona["close"] > vela_zona["open"] and
        vela_confirmacion["close"] > vela_confirmacion["open"]
    )

    # ==========================
    # 🔥 CONTINUIDAD (BREAKOUT)
    # ==========================
    rompe_resistencia = (
        vela_zona["close"] > resistencia and
        vela_confirmacion["close"] > vela_zona["close"]
    )

    rompe_soporte = (
        vela_zona["close"] < soporte and
        vela_confirmacion["close"] < vela_zona["close"]
    )

    # ==========================
    # 🔻 PUT (venta)
    # ==========================
    if rechazo_resistencia:
        return {"action": "put"}

    if tendencia_bajista and rompe_soporte:
        return {"action": "put"}

    # ==========================
    # 🔺 CALL (compra)
    # ==========================
    if rechazo_soporte:
        return {"action": "call"}

    if tendencia_alcista and rompe_resistencia:
        return {"action": "call"}

    return None
