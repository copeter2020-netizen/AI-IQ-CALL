import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas or len(velas) < 4:
        return None

    # 🔥 SOLO VELAS CERRADAS
    c1 = velas[-2]  # última vela cerrada
    c2 = velas[-3]  # vela anterior real

    max_prev = max(v["max"] for v in velas[:-2])
    min_prev = min(v["min"] for v in velas[:-2])

    # ==========================
    # 🔥 VALIDAR TRAMPA (solo filtro)
    # ==========================
    hay_trampa = (
        (c1["max"] > max_prev and c1["close"] < c1["open"]) or
        (c1["min"] < min_prev and c1["close"] > c1["open"])
    )

    if not hay_trampa:
        return None

    # ==========================
    # 🔒 CONTINUIDAD REAL
    # ==========================

    # 🟢 VERDE → CALL
    if c2["close"] > c2["open"]:
        return {"action": "call"}

    # 🔴 ROJA → PUT
    if c2["close"] < c2["open"]:
        return {"action": "put"}

    return None
