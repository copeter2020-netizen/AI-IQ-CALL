def analizar_price_action(candles):

    if len(candles) < 10:
        return None

    c1 = candles[-1]
    c2 = candles[-2]
    c3 = candles[-3]
    c4 = candles[-4]
    c5 = candles[-5]

    score = 0

    # ==========================
    # FILTRO INDECISIÓN
    # ==========================
    if indecision(c1):
        return None

    # ==========================
    # COMPRA (CALL)
    # ==========================
    if (
        c5["close"] < c4["close"] < c3["close"] and
        c2["close"] < c2["open"] and
        c1["close"] > c1["open"] and
        c1["close"] > c3["close"]
    ):
        score += 4

        if fuerte(c1):
            score += 2

        if micro_alcista(candles):
            score += 2

        return {"action": "call", "score": score}

    # ==========================
    # VENTA (PUT)
    # ==========================
    if (
        c5["close"] > c4["close"] > c3["close"] and
        c2["close"] > c2["open"] and
        c1["close"] < c1["open"] and
        c1["close"] < c3["close"]
    ):
        score += 4

        if fuerte(c1):
            score += 2

        if micro_bajista(candles):
            score += 2

        return {"action": "put", "score": score}

    return None


# ==========================
# FUNCIONES AUX
# ==========================
def fuerte(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo > rango * 0.6


def indecision(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo < rango * 0.3


def micro_alcista(c):
    return c[-1]["close"] > c[-2]["close"] > c[-3]["close"]


def micro_bajista(c):
    return c[-1]["close"] < c[-2]["close"] < c[-3]["close"]
