def calcular_rsi(candles, periodo=14):

    closes = [c["close"] for c in candles]

    ganancias = []
    perdidas = []

    for i in range(1, len(closes)):
        cambio = closes[i] - closes[i - 1]

        if cambio > 0:
            ganancias.append(cambio)
            perdidas.append(0)
        else:
            ganancias.append(0)
            perdidas.append(abs(cambio))

    avg_gain = sum(ganancias[-periodo:]) / periodo
    avg_loss = sum(perdidas[-periodo:]) / periodo

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def detectar_reversion_extrema(candles):

    if len(candles) < 20:
        return None

    c1 = candles[-1]
    c2 = candles[-2]

    cuerpo = abs(c1["close"] - c1["open"])
    rango = c1["max"] - c1["min"]

    if rango == 0:
        return None

    # 🔥 RSI
    rsi = calcular_rsi(candles)

    # 🔥 MECHAS
    mecha_sup = c1["max"] - max(c1["open"], c1["close"])
    mecha_inf = min(c1["open"], c1["close"]) - c1["min"]

    # ==========================
    # 🔻 REVERSIÓN ALCISTA
    # ==========================
    if (
        c1["min"] < c2["min"] and
        mecha_inf > cuerpo * 1.5 and
        c1["close"] > c1["open"] and
        rsi < 30 and
        c2["close"] < c2["open"]
    ):
        return {
            "action": "call",
            "score": 5
        }

    # ==========================
    # 🔺 REVERSIÓN BAJISTA
    # ==========================
    if (
        c1["max"] > c2["max"] and
        mecha_sup > cuerpo * 1.5 and
        c1["close"] < c1["open"] and
        rsi > 70 and
        c2["close"] > c2["open"]
    ):
        return {
            "action": "put",
            "score": 5
        }

    return None
