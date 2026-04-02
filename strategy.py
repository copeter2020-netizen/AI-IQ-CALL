import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 30, time.time())

    if not velas or len(velas) < 10:
        return None

    # 🔥 VELA DE TRAMPA (cerrada)
    vela_trampa = velas[-2]

    # 🔥 HISTORIAL PARA NIVELES
    historial = velas[:-2]

    max_prev = max(v["max"] for v in historial)
    min_prev = min(v["min"] for v in historial)

    # 🔥 CUERPO Y MECHAS
    cuerpo = abs(vela_trampa["close"] - vela_trampa["open"])
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    # ==========================
    # 🔻 TRAMPA BAJISTA → CALL
    # ==========================
    if (
        vela_trampa["min"] < min_prev and            # rompe soporte
        vela_trampa["close"] > vela_trampa["open"] and
        mecha_inf > cuerpo * 1.5                     # rechazo fuerte
    ):
        return {"action": "call"}

    # ==========================
    # 🔺 TRAMPA ALCISTA → PUT
    # ==========================
    if (
        vela_trampa["max"] > max_prev and            # rompe resistencia
        vela_trampa["close"] < vela_trampa["open"] and
        mecha_sup > cuerpo * 1.5                     # rechazo fuerte
    ):
        return {"action": "put"}

    return None
