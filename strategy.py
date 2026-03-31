import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas or len(velas) < 3:
        return None

    c1 = velas[-1]  # vela actual
    c2 = velas[-2]  # 🔥 vela anterior (MANDA)

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔥 DETECTAR TRAMPA (NO CAMBIA)
    # ==========================
    trampa = (
        (c1["max"] > max_prev and c1["close"] < c1["open"]) or
        (c1["min"] < min_prev and c1["close"] > c1["open"])
    )

    if not trampa:
        return None

    # ==========================
    # 🔥 CONTINUIDAD OBLIGATORIA
    # ==========================

    # 🟢 VELA VERDE → CALL
    if c2["close"] > c2["open"]:
        return {"action": "call"}

    # 🔴 VELA ROJA → PUT
    if c2["close"] < c2["open"]:
        return {"action": "put"}

    return None
