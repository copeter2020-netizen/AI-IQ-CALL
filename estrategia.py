def calculate_indicators(df):
    # NO usamos indicadores → solo estructura
    return df


def is_doji(candle):
    body = abs(candle["close"] - candle["open"])
    rango = candle["high"] - candle["low"]
    return body < (rango * 0.2)


def fuerza_candle(candle):
    body = abs(candle["close"] - candle["open"])
    rango = candle["high"] - candle["low"]

    if rango == 0:
        return 0

    return body / rango


def tendencia(df):
    # últimos 5 cierres
    closes = df["close"].values[-6:]

    alcista = all(closes[i] > closes[i-1] for i in range(1, len(closes)))
    bajista = all(closes[i] < closes[i-1] for i in range(1, len(closes)))

    if alcista:
        return "call"
    elif bajista:
        return "put"
    else:
        return None


def check_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # ❌ FILTROS DUROS
    if is_doji(last):
        return None

    if fuerza_candle(last) < 0.6:
        return None

    trend = tendencia(df)

    if trend is None:
        return None

    # ✔ CONTINUIDAD REAL
    if trend == "call" and last["close"] > prev["close"]:
        return "call"

    if trend == "put" and last["close"] < prev["close"]:
        return "put"

    return None


def score_pair(df):
    last = df.iloc[-1]

    score = 0

    # fuerza
    if fuerza_candle(last) > 0.7:
        score += 2
    elif fuerza_candle(last) > 0.6:
        score += 1

    # continuidad fuerte
    closes = df["close"].values[-4:]

    if closes[-1] > closes[-2] > closes[-3]:
        score += 1

    if closes[-1] < closes[-2] < closes[-3]:
        score += 1

    return score
