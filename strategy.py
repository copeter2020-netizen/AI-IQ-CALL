def calcular_macd(candles):

    closes = [c["close"] for c in candles]

    ema12 = ema(closes, 12)
    ema26 = ema(closes, 26)

    macd = [a - b for a, b in zip(ema12, ema26)]
    signal = ema(macd, 9)

    return macd, signal


def ema(data, period):

    ema_values = []
    k = 2 / (period + 1)

    ema_values.append(data[0])

    for i in range(1, len(data)):
        ema_values.append(data[i] * k + ema_values[-1] * (1 - k))

    return ema_values


# ==========================
# RUPTURAS
# ==========================
def ruptura_resistencia(candles):
    highs = [c["max"] for c in candles[-6:-1]]
    return candles[-1]["close"] > max(highs)


def ruptura_soporte(candles):
    lows = [c["min"] for c in candles[-6:-1]]
    return candles[-1]["close"] < min(lows)


# ==========================
# CONTINUIDAD
# ==========================
def continuidad_alcista(c):
    return c[-1]["close"] > c[-2]["close"] > c[-3]["close"]


def continuidad_bajista(c):
    return c[-1]["close"] < c[-2]["close"] < c[-3]["close"]


# ==========================
# CRUCE MACD
# ==========================
def cruce_alcista(macd, signal):
    return macd[-2] < signal[-2] and macd[-1] > signal[-1]


def cruce_bajista(macd, signal):
    return macd[-2] > signal[-2] and macd[-1] < signal[-1]


# ==========================
# ESTRATEGIA PRINCIPAL
# ==========================
def analizar_macd_price_action(candles):

    if len(candles) < 30:
        return None

    macd, signal = calcular_macd(candles)

    score = 0

    # ==========================
    # COMPRA
    # ==========================
    if (
        ruptura_resistencia(candles) and
        continuidad_alcista(candles) and
        cruce_alcista(macd, signal)
    ):
        score += 5

        if macd[-1] > signal[-1]:
            score += 2

        return {"action": "call", "score": score}

    # ==========================
    # VENTA
    # ==========================
    if (
        ruptura_soporte(candles) and
        continuidad_bajista(candles) and
        cruce_bajista(macd, signal)
    ):
        score += 5

        if macd[-1] < signal[-1]:
            score += 2

        return {"action": "put", "score": score}

    return None
