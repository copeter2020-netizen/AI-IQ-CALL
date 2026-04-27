# estrategia.py

def es_doji(candle):
    body = abs(candle["close"] - candle["open"])
    rango = candle["max"] - candle["min"]
    return body < (rango * 0.2)


def es_fuerte(candle):
    body = abs(candle["close"] - candle["open"])
    rango = candle["max"] - candle["min"]
    return body > (rango * 0.6)


def direccion(candle):
    if candle["close"] > candle["open"]:
        return "call"
    elif candle["close"] < candle["open"]:
        return "put"
    return None


def continuidad(candles):
    if len(candles) < 3:
        return None

    c1, c2, c3 = candles[-3], candles[-2], candles[-1]

    dir1 = direccion(c1)
    dir2 = direccion(c2)
    dir3 = direccion(c3)

    # misma dirección + fuerza
    if dir1 == dir2 == dir3:
        if es_fuerte(c3) and not es_doji(c3):
            return dir3

    return None


def check_signal(candles):
    """
    SOLO continuidad limpia
    """
    signal = continuidad(candles)
    return signal


def score_pair(candles):
    """
    Filtro de calidad
    """
    if len(candles) < 5:
        return 0

    ultimas = candles[-5:]

    fuertes = sum(1 for c in ultimas if es_fuerte(c))
    dojis = sum(1 for c in ultimas if es_doji(c))

    score = fuertes - dojis

    return score
