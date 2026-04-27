# estrategia.py
# SNIPER CONTINUIDAD PURO (SIN INDICADORES)

def es_doji(candle):
    cuerpo = abs(candle['close'] - candle['open'])
    rango = candle['max'] - candle['min']
    return cuerpo < (rango * 0.2)


def es_fuerte(candle):
    cuerpo = abs(candle['close'] - candle['open'])
    rango = candle['max'] - candle['min']
    return cuerpo > (rango * 0.6)


def direccion(candle):
    return "call" if candle['close'] > candle['open'] else "put"


def continuidad(candles):
    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]

    # Evitar indecisión
    if es_doji(c3):
        return None, 0

    # Evitar vela débil
    if not es_fuerte(c3):
        return None, 0

    dir1 = direccion(c1)
    dir2 = direccion(c2)
    dir3 = direccion(c3)

    # Continuidad fuerte (3 velas misma dirección)
    if dir1 == dir2 == dir3:
        return dir3, 1.0

    # Continuidad parcial (2 velas + fuerza)
    if dir2 == dir3:
        return dir3, 0.75

    return None, 0


def check_signal(candles):
    if len(candles) < 3:
        return None

    signal, fuerza = continuidad(candles)

    if signal and fuerza >= 0.75:
        return signal

    return None


def score_pair(candles):
    if len(candles) < 5:
        return 0

    score = 0

    ultimas = candles[-5:]

    for c in ultimas:
        if not es_doji(c):
            score += 1

    # fuerza de tendencia
    dirs = [direccion(c) for c in ultimas]

    if dirs.count("call") > 3 or dirs.count("put") > 3:
        score += 2

    return score
