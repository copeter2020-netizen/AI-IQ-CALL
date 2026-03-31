import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas or len(velas) < 3:
        return None

    c1 = velas[-1]  # vela actual
    c2 = velas[-2]  # 🔥 vela anterior

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # 🔻 CALL
    if (
        c1["max"] > max_prev and
        c1["close"] < c1["open"] and
        (c1["max"] - c1["close"]) > abs(c1["close"] - c1["open"])
    ):
        # 🔒 SOLO vela verde
        if c2["close"] > c2["open"]:
            return {"action": "call"}
        return None

    # 🔺 PUT
    if (
        c1["min"] < min_prev and
        c1["close"] > c1["open"] and
        (c1["close"] - c1["min"]) > abs(c1["close"] - c1["open"])
    ):
        # 🔒 SOLO vela roja
        if c2["close"] < c2["open"]:
            return {"action": "put"}
        return None

    return None
