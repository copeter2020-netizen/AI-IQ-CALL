def calcular_macd(candles):

    closes = [c["close"] for c in candles]

    ema12 = []
    ema26 = []

    for i, price in enumerate(closes):

        if i == 0:
            ema12.append(price)
            ema26.append(price)
        else:
            ema12.append((price * 0.15) + ema12[-1] * 0.85)
            ema26.append((price * 0.075) + ema26[-1] * 0.925)

    macd = [ema12[i] - ema26[i] for i in range(len(closes))]

    signal = []
    for i, m in enumerate(macd):
        if i == 0:
            signal.append(m)
        else:
            signal.append((m * 0.2) + signal[-1] * 0.8)

    return macd, signal


def fuerza_vela(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo > (rango * 0.6)


def sin_mechas(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    return cuerpo >= (rango * 0.7)


def continuidad(candles):
    c1 = candles[-1]
    c2 = candles[-2]

    return (
        (c1["close"] > c1["open"] and c2["close"] > c2["open"]) or
        (c1["close"] < c1["open"] and c2["close"] < c2["open"])
    )


def ruptura_resistencia(candles):
    highs = [c["max"] for c in candles[-15:-1]]
    return candles[-1]["close"] > max(highs)


def ruptura_soporte(candles):
    lows = [c["min"] for c in candles[-15:-1]]
    return candles[-1]["close"] < min(lows)


def analizar_macd_price_action(candles):

    if len(candles) < 30:
        return None

    macd, signal = calcular_macd(candles)

    c1 = candles[-1]

    score = 0

    # CALL
    if ruptura_resistencia(candles):
        score += 2

    if macd[-2] < signal[-2] and macd[-1] > signal[-1]:
        score += 2

    if c1["close"] > c1["open"]:
        score += 1

    if fuerza_vela(c1):
        score += 2

    if continuidad(candles):
        score += 1

    if sin_mechas(c1):
        score += 1

    if score >= 5:
        return {"action": "call", "score": score}

    # PUT
    score = 0

    if ruptura_soporte(candles):
        score += 2

    if macd[-2] > signal[-2] and macd[-1] < signal[-1]:
        score += 2

    if c1["close"] < c1["open"]:
        score += 1

    if fuerza_vela(c1):
        score += 2

    if continuidad(candles):
        score += 1

    if sin_mechas(c1):
        score += 1

    if score >= 5:
        return {"action": "put", "score": score}

    return None
