import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas or len(velas) < 3:
        return None

    c1 = velas[-1]  # vela actual
    c2 = velas[-2]  # 🔥 vela anterior (REGLA OBLIGATORIA)

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔻 TRAMPA → CALL
    # ==========================
    if (
        c1["max"] > max_prev and
        c1["close"] < c1["open"] and
        (c1["max"] - c1["close"]) > abs(c1["close"] - c1["open"])
    ):
        # 🔒 BLOQUEO TOTAL
        if not (c2["close"] > c2["open"]):
            return None

        return {"action": "call"}

    # ==========================
    # 🔺 TRAMPA → PUT
    # ==========================
    if (
        c1["min"] < min_prev and
        c1["close"] > c1["open"] and
        (c1["close"] - c1["min"]) > abs(c1["close"] - c1["open"])
    ):
        # 🔒 BLOQUEO TOTAL
        if not (c2["close"] < c2["open"]):
            return None

        return {"action": "put"}

    return None
