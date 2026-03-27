# ==========================
# DETECTAR MEJOR OPORTUNIDAD
# ==========================
def detectar_oportunidad(candles):

    if len(candles) < 10:
        return None, 0

    score = 0

    c1 = candles[-1]
    c2 = candles[-2]
    c3 = candles[-3]
    c4 = candles[-4]
    c5 = candles[-5]

    # ==========================
    # 🔥 FILTRO: EVITAR INDECISIÓN
    # ==========================
    if es_indecision(c1):
        return None, 0

    # ==========================
    # 🔺 COMPRA (CALL)
    # ==========================
    if (
        c5["close"] < c4["close"] < c3["close"] and  # tendencia
        c2["close"] < c2["open"] and                # retroceso rojo
        c1["close"] > c1["open"] and                # confirmación verde
        c1["close"] > c3["close"]                   # rompimiento
    ):
        score += 3

        if es_fuerte(c1):
            score += 2

        if continuidad_alcista(candles):
            score += 2

        return "call", score

    # ==========================
    # 🔻 VENTA (PUT)
    # ==========================
    if (
        c5["close"] > c4["close"] > c3["close"] and
        c2["close"] > c2["open"] and
        c1["close"] < c1["open"] and
        c1["close"] < c3["close"]
    ):
        score += 3

        if es_fuerte(c1):
            score += 2

        if continuidad_bajista(candles):
            score += 2

        return "put", score

    return None, 0


# ==========================
# FUNCIONES AUXILIARES
# ==========================
def es_fuerte(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo > rango * 0.6


def es_indecision(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo < rango * 0.3


def continuidad_alcista(candles):
    return (
        candles[-1]["close"] > candles[-2]["close"] > candles[-3]["close"]
    )


def continuidad_bajista(candles):
    return (
        candles[-1]["close"] < candles[-2]["close"] < candles[-3]["close"]
    )
