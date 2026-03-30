import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas:
        return None

    c1 = velas[-1]

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔻 TRAMPA ALCISTA (ANTES PUT → AHORA CALL)
    # ==========================
    if (
        c1["max"] > max_prev and
        c1["close"] < c1["open"] and
        (c1["max"] - c1["close"]) > abs(c1["close"] - c1["open"])
    ):
        return {"action": "call"}  # 🔥 INVERTIDO

    # ==========================
    # 🔺 TRAMPA BAJISTA (ANTES CALL → AHORA PUT)
    # ==========================
    if (
        c1["min"] < min_prev and
        c1["close"] > c1["open"] and
        (c1["close"] - c1["min"]) > abs(c1["close"] - c1["open"])
    ):
        return {"action": "put"}  # 🔥 INVERTIDO

    return None
