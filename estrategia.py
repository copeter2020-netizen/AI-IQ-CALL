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
# FILTRO INTELIGENTE FLEXIBLE
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    # ❌ SOLO eliminar doji real
    if last["body"] < last["range"] * 0.15:
        return None

    # =========================
    # 🔥 CONTINUIDAD FUERTE
    # =========================
    if last["direction"] == prev["direction"]:

        # continuación clásica
        if last["direction"] == "call" and last["close"] > prev["close"]:
            return "call"

        if last["direction"] == "put" and last["close"] < prev["close"]:
            return "put"

    # =========================
    # ⚡ CONTINUIDAD SUAVE (NUEVO)
    # =========================
    if prev["direction"] == prev2["direction"]:

        if prev["direction"] == "call" and last["close"] > prev["open"]:
            return "call"

        if prev["direction"] == "put" and last["close"] < prev["open"]:
            return "put"

    # =========================
    # 🚀 MICRO RUPTURA (NUEVO)
    # =========================
    if last["direction"] == "call" and last["close"] > prev["high"]:
        return "call"

    if last["direction"] == "put" and last["close"] < prev["low"]:
        return "put"

    return None


# =========================
# SCORE MEJORADO
# =========================
def score_pair(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    score = 0

    # continuidad
    if last["direction"] == prev["direction"]:
        score += 1

    # tendencia (3 velas)
    if last["direction"] == prev["direction"] == prev2["direction"]:
        score += 2

    # expansión real
    if last["range"] > prev["range"]:
        score += 1

    # ruptura
    if last["close"] > prev["high"] or last["close"] < prev["low"]:
        score += 1

    return score
