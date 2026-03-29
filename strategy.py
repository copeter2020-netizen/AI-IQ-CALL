import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas:
        return None

    c1 = velas[-1]
    c2 = velas[-2]
    c3 = velas[-3]

    # 🔥 máximos y mínimos recientes
    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔻 TRAMPA ALCISTA (FAKE BREAK ARRIBA → PUT)
    # ==========================
    if (
        c1["max"] > max_prev and  # rompe máximo
        c1["close"] < c1["open"] and  # cierra rojo
        (c1["max"] - c1["close"]) > abs(c1["close"] - c1["open"])  # mecha superior fuerte
    ):
        return {"action": "put"}

    # ==========================
    # 🔺 TRAMPA BAJISTA (FAKE BREAK ABAJO → CALL)
    # ==========================
    if (
        c1["min"] < min_prev and  # rompe mínimo
        c1["close"] > c1["open"] and  # cierra verde
        (c1["close"] - c1["min"]) > abs(c1["close"] - c1["open"])  # mecha inferior fuerte
    ):
        return {"action": "call"}

    return None
