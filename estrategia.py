def calculate_indicators(candles):
    data = []

    for c in candles:
        open_ = c["open"]
        close = c["close"]
        high = c["max"]
        low = c["min"]

        body = abs(close - open_)
        range_ = high - low if high - low != 0 else 1e-6

        direction = "call" if close > open_ else "put"

        data.append({
            "open": open_,
            "close": close,
            "high": high,
            "low": low,
            "body": body,
            "range": range_,
            "direction": direction
        })

    return data


# =========================
# SEÑAL FLEXIBLE (CLAVE)
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]

    # ❌ SOLO eliminar doji real (muy pequeño)
    if last["body"] < last["range"] * 0.15:
        return None

    # =========================
    # CONTINUIDAD SIMPLE
    # =========================
    if last["direction"] == prev["direction"]:

        # CALL
        if last["direction"] == "call" and last["close"] > prev["close"]:
            return "call"

        # PUT
        if last["direction"] == "put" and last["close"] < prev["close"]:
            return "put"

    return None


# =========================
# SCORE MÁS INTELIGENTE
# =========================
def score_pair(data):

    score = 0

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    # continuidad
    if last["direction"] == prev["direction"]:
        score += 1

    # 3 velas misma dirección (tendencia)
    if last["direction"] == prev["direction"] == prev2["direction"]:
        score += 2

    # expansión (movimiento real)
    if last["range"] > prev["range"]:
        score += 1

    return score
