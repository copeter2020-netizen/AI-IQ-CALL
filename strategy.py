import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 30, time.time())

    if not velas or len(velas) < 5:
        return None

    # 🔥 SOLO VELAS CERRADAS
    vela_trampa = velas[-2]
    vela_anterior = velas[-3]

    max_prev = max(v["max"] for v in velas[:-2])
    min_prev = min(v["min"] for v in velas[:-2])

    # 🔥 FILTRO TRAMPA (OBLIGATORIO)
    hay_trampa = (
        (vela_trampa["max"] > max_prev and vela_trampa["close"] < vela_trampa["open"]) or
        (vela_trampa["min"] < min_prev and vela_trampa["close"] > vela_trampa["open"])
    )

    if not hay_trampa:
        return None

    # 🔒 CONTINUIDAD PURA (MANDATO)
    if vela_anterior["close"] > vela_anterior["open"]:
        return {"action": "call"}

    if vela_anterior["close"] < vela_anterior["open"]:
        return {"action": "put"}

    return None
