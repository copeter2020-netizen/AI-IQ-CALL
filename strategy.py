def analizar_institucional(candles):

    if len(candles) < 20:
        return None

    c = candles[-1]
    prev = candles[-2]

    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]

    if rango == 0:
        return None

    fuerza = cuerpo / rango

    score = 0

    # ==========================
    # 🔥 DETECTAR MANIPULACIÓN
    # ==========================
    fake_break_up = (
        c["max"] > prev["max"] and
        c["close"] < prev["max"]
    )

    fake_break_down = (
        c["min"] < prev["min"] and
        c["close"] > prev["min"]
    )

    rechazo_superior = (c["max"] - max(c["open"], c["close"])) > cuerpo
    rechazo_inferior = (min(c["open"], c["close"]) - c["min"]) > cuerpo

    # ==========================
    # 🔥 COMPRA (TRAMPA BAJISTA)
    # ==========================
    if fake_break_down and rechazo_inferior:

        score += 3

        if fuerza > 0.6:
            score += 2

        if c["close"] > c["open"]:
            score += 1

        return {
            "action": "call",
            "score": score
        }

    # ==========================
    # 🔥 VENTA (TRAMPA ALCISTA)
    # ==========================
    if fake_break_up and rechazo_superior:

        score += 3

        if fuerza > 0.6:
            score += 2

        if c["close"] < c["open"]:
            score += 1

        return {
            "action": "put",
            "score": score
        }

    return None
