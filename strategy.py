import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 50, time.time())

    if not velas or len(velas) < 15:
        return None

    # 🔥 VELA DE TRAMPA (cerrada)
    vela = velas[-2]

    historial = velas[:-2]

    max_prev = max(v["max"] for v in historial)
    min_prev = min(v["min"] for v in historial)

    # ==========================
    # 🔥 CUERPO Y MECHAS
    # ==========================
    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return None

    mecha_sup = vela["max"] - max(vela["close"], vela["open"])
    mecha_inf = min(vela["close"], vela["open"]) - vela["min"]

    # ==========================
    # 🔥 FILTRO DOJI (FUERTE)
    # ==========================
    if cuerpo < rango * 0.35:
        return None

    # ==========================
    # 🔥 FILTRO FUERZA (EVITA VELAS DÉBILES)
    # ==========================
    if cuerpo < (rango * 0.5):
        return None

    # ==========================
    # 🔻 TRAMPA BAJISTA → CALL
    # ==========================
    if (
        vela["min"] < min_prev and           # rompe soporte
        vela["close"] > vela["open"] and     # cierra verde
        mecha_inf > cuerpo * 1.8             # rechazo fuerte real
    ):
        return {"action": "call"}

    # ==========================
    # 🔺 TRAMPA ALCISTA → PUT
    # ==========================
    if (
        vela["max"] > max_prev and           # rompe resistencia
        vela["close"] < vela["open"] and     # cierra roja
        mecha_sup > cuerpo * 1.8             # rechazo fuerte real
    ):
        return {"action": "put"}

    return None
