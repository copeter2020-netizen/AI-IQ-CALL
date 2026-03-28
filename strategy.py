def calcular_ema(candles, periodo=10):
    precios = [c["close"] for c in candles]

    if len(precios) < periodo:
        return None

    k = 2 / (periodo + 1)
    ema = precios[0]

    for p in precios:
        ema = p * k + ema * (1 - k)

    return ema


def analizar_vela_apertura(candles):

    if len(candles) < 15:
        return None

    ultima = candles[-1]

    apertura = ultima["open"]
    cierre = ultima["close"]
    maximo = ultima["max"]
    minimo = ultima["min"]

    cuerpo = abs(cierre - apertura)
    rango = maximo - minimo

    if rango == 0:
        return None

    fuerza = cuerpo / rango

    # 🔥 FILTRO: vela fuerte
    if fuerza < 0.6:
        return None

    # 🔥 EMA tendencia
    ema = calcular_ema(candles[:-1], 10)

    if not ema:
        return None

    score = 0

    # ==========================
    # 🔥 COMPRA
    # ==========================
    if cierre > apertura and cierre > ema:

        score += 2

        if fuerza > 0.7:
            score += 2

        if maximo > candles[-2]["max"]:
            score += 1

        return {
            "action": "call",
            "score": score
        }

    # ==========================
    # 🔥 VENTA
    # ==========================
    if cierre < apertura and cierre < ema:

        score += 2

        if fuerza > 0.7:
            score += 2

        if minimo < candles[-2]["min"]:
            score += 1

        return {
            "action": "put",
            "score": score
        }

    return None
