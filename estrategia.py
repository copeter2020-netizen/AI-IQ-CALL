# estrategia.py

def calculate_indicators(candles):
    data = []

    for c in candles:
        o = c["open"]
        c_ = c["close"]
        h = c["max"]
        l = c["min"]

        body = abs(c_ - o)
        range_ = h - l if h - l != 0 else 1e-6

        direction = "call" if c_ > o else "put"

        data.append({
            "open": o,
            "close": c_,
            "high": h,
            "low": l,
            "body": body,
            "range": range_,
            "direction": direction
        })

    return data


# =========================
# ANALISIS PRICE ACTION
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    body_ratio = last["body"] / last["range"]

    # ❌ evitar indecisión
    if body_ratio < 0.2:
        return None

    # =========================
    # 🔥 CONTINUIDAD
    # =========================
    if last["direction"] == prev["direction"]:

        # impulso real
        if body_ratio > 0.5:

            if last["direction"] == "call" and last["close"] > prev["close"]:
                return "call"

            if last["direction"] == "put" and last["close"] < prev["close"]:
                return "put"

    # =========================
    # ⚡ REVERSIÓN (rechazo fuerte)
    # =========================
    upper_wick = last["high"] - max(last["open"], last["close"])
    lower_wick = min(last["open"], last["close"]) - last["low"]

    # rechazo arriba → PUT
    if upper_wick > last["body"] * 1.5:
        return "put"

    # rechazo abajo → CALL
    if lower_wick > last["body"] * 1.5:
        return "call"

    return None


# =========================
# SCORE DE CALIDAD
# =========================
def score_pair(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    score = 0

    # fuerza
    if last["body"] > prev["body"]:
        score += 1

    # continuidad
    if last["direction"] == prev["direction"]:
        score += 1

    # tendencia (3 velas)
    if last["direction"] == prev["direction"] == prev2["direction"]:
        score += 1

    # expansión
    if last["range"] > prev["range"]:
        score += 1

    return score
