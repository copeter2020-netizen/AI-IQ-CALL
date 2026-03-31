import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas:
        return None

    c1 = velas[-1]   # vela actual (trampa)
    c2 = velas[-2]   # 🔥 vela anterior (confirmación)

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔻 TRAMPA ALCISTA → CALL
    # ==========================
    if (
        c1["max"] > max_prev and
        c1["close"] < c1["open"] and
        (c1["max"] - c1["close"]) > abs(c1["close"] - c1["open"])
    ):

        # 🔥 CONFIRMACIÓN: vela anterior VERDE
        if c2["close"] > c2["open"]:
            return {"action": "call"}

    # ==========================
    # 🔺 TRAMPA BAJISTA → PUT
    # ==========================
    if (
        c1["min"] < min_prev and
        c1["close"] > c1["open"] and
        (c1["close"] - c1["min"]) > abs(c1["close"] - c1["open"])
    ):

        # 🔥 CONFIRMACIÓN: vela anterior ROJA
        if c2["close"] < c2["open"]:
            return {"action": "put"}

    return None
