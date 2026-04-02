import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 30, time.time())

    if not velas or len(velas) < 6:
        return None

    vela_trampa = velas[-3]      # trampa
    vela_confirm = velas[-2]     # confirmación
    vela_base = velas[-4]        # dirección

    max_prev = max(v["max"] for v in velas[:-3])
    min_prev = min(v["min"] for v in velas[:-3])

    # ==========================
    # 🔥 DETECTAR TRAMPA
    # ==========================
    hay_trampa = (
        (vela_trampa["max"] > max_prev and vela_trampa["close"] < vela_trampa["open"]) or
        (vela_trampa["min"] < min_prev and vela_trampa["close"] > vela_trampa["open"])
    )

    if not hay_trampa:
        return None

    # ==========================
    # 🔥 DIRECCIÓN BASE (INVERTIDA)
    # ==========================
    if vela_base["close"] > vela_base["open"]:
        direccion = "put"
    elif vela_base["close"] < vela_base["open"]:
        direccion = "call"
    else:
        return None

    # ==========================
    # 🔥 CONFIRMACIÓN MISMO COLOR
    # ==========================
    if direccion == "call" and vela_confirm["close"] > vela_confirm["open"]:
        return {"action": "call"}

    if direccion == "put" and vela_confirm["close"] < vela_confirm["open"]:
        return {"action": "put"}

    return None 
