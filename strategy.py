def detectar_reversion(candles):

    if len(candles) < 10:
        return None

    c = candles[-1]
    prev = candles[-2]

    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]

    if rango == 0:
        return None

    score = 0

    # ==========================
    # 🔥 DETECTAR AGOTAMIENTO
    # ==========================
    fuerza = cuerpo / rango

    # 🔥 MECHAS
    mecha_sup = c["max"] - max(c["open"], c["close"])
    mecha_inf = min(c["open"], c["close"]) - c["min"]

    # ==========================
    # 🔻 REVERSIÓN ALCISTA (CALL)
    # ==========================
    barrido_bajo = c["min"] < prev["min"]

    if barrido_bajo and mecha_inf > cuerpo * 1.5:

        score += 3

        if c["close"] > c["open"]:
            score += 2

        if fuerza > 0.5:
            score += 1

        return {
            "action": "call",
            "score": score
        }

    # ==========================
    # 🔺 REVERSIÓN BAJISTA (PUT)
    # ==========================
    barrido_alto = c["max"] > prev["max"]

    if barrido_alto and mecha_sup > cuerpo * 1.5:

        score += 3

        if c["close"] < c["open"]:
            score += 2

        if fuerza > 0.5:
            score += 1

        return {
            "action": "put",
            "score": score
        }

    return None
