def calculate_indicators(candles):
    # Convertimos a estructura simple
    data = []

    for c in candles:
        open_ = c["open"]
        close = c["close"]
        high = c["max"]
        low = c["min"]

        body = abs(close - open_)
        wick = (high - low) - body
        direction = "call" if close > open_ else "put"

        data.append({
            "open": open_,
            "close": close,
            "high": high,
            "low": low,
            "body": body,
            "wick": wick,
            "direction": direction
        })

    return data


# =========================
# FILTRO PRINCIPAL
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    # =========================
    # ❌ FILTROS DE BASURA
    # =========================

    # DOJI (sin cuerpo)
    if last["body"] < (last["high"] - last["low"]) * 0.3:
        return None

    # WICK dominante (indecisión)
    if last["wick"] > last["body"] * 1.2:
        return None

    # RANGO MUERTO (muy poco movimiento)
    if last["body"] < prev["body"] * 0.6:
        return None

    # =========================
    # 🔥 CONTINUIDAD REAL
    # =========================

    # CALL fuerte
    if (
        last["direction"] == "call"
        and prev["direction"] == "call"
        and last["close"] > prev["close"]
    ):
        return "call"

    # PUT fuerte
    if (
        last["direction"] == "put"
        and prev["direction"] == "put"
        and last["close"] < prev["close"]
    ):
        return "put"

    return None


# =========================
# SCORE INTELIGENTE
# =========================
def score_pair(data):

    score = 0

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    # Fuerza del cuerpo
    if last["body"] > prev["body"]:
        score += 1

    # Continuidad
    if last["direction"] == prev["direction"]:
        score += 1

    # Momentum (3 velas)
    if (
        last["direction"] == prev["direction"] ==
        prev2["direction"]
    ):
        score += 1

    # Expansión real
    if (last["high"] - last["low"]) > (prev["high"] - prev["low"]):
        score += 1

    return score
