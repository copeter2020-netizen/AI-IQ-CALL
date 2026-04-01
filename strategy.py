import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 40, time.time())

    if not velas or len(velas) < 10:
        return None

    # 🔥 VELAS CLAVE
    vela_base = velas[-4]
    vela_trampa = velas[-3]
    vela_confirm = velas[-2]

    historial = velas[:-3]

    max_prev = max(v["max"] for v in historial)
    min_prev = min(v["min"] for v in historial)

    # ==========================
    # 🔥 FILTRO DOJI (FUERTE)
    # ==========================
    cuerpo_confirm = abs(vela_confirm["close"] - vela_confirm["open"])
    rango_confirm = vela_confirm["max"] - vela_confirm["min"]

    if rango_confirm == 0 or cuerpo_confirm < (rango_confirm * 0.4):
        return None

    # ==========================
    # 🔥 RECHAZO EN TRAMPA
    # ==========================
    cuerpo_trampa = abs(vela_trampa["close"] - vela_trampa["open"])
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    # ==========================
    # 🔻 TRAMPA BAJISTA → CALL (INVERTIDO)
    # ==========================
    if (
        vela_trampa["min"] < min_prev and                # rompe soporte
        vela_trampa["close"] > vela_trampa["open"] and  # cierra verde
        mecha_inf > cuerpo_trampa * 1.5                 # rechazo fuerte
    ):

        # 🔥 CONFIRMACIÓN VERDE FUERTE
        if vela_confirm["close"] > vela_confirm["open"]:
            return {"action": "call"}

    # ==========================
    # 🔺 TRAMPA ALCISTA → PUT (INVERTIDO)
    # ==========================
    if (
        vela_trampa["max"] > max_prev and                # rompe resistencia
        vela_trampa["close"] < vela_trampa["open"] and  # cierra roja
        mecha_sup > cuerpo_trampa * 1.5                 # rechazo fuerte
    ):

        # 🔥 CONFIRMACIÓN ROJA FUERTE
        if vela_confirm["close"] < vela_confirm["open"]:
            return {"action": "put"}

    return None
