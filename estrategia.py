# estrategia.py

def calculate_indicators(candles):
    data = []

    for c in candles:
        o = c["open"]
        cl = c["close"]
        h = c["max"]
        l = c["min"]

        body = abs(cl - o)
        range_ = h - l if h - l != 0 else 1e-6

        direction = "call" if cl > o else "put"

        data.append({
            "open": o,
            "close": cl,
            "high": h,
            "low": l,
            "body": body,
            "range": range_,
            "direction": direction
        })

    return data


# =========================
# ULTRA SEÑAL (MUCHAS ENTRADAS)
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    body_ratio = last["body"] / last["range"]

    # ❌ SOLO eliminar doji extremo
    if body_ratio < 0.08:
        return None

    # =========================
    # 1. CONTINUIDAD FUERTE
    # =========================
    if last["direction"] == prev["direction"]:
        return last["direction"]

    # =========================
    # 2. CONTINUIDAD SUAVE
    # =========================
    if prev["direction"] == prev2["direction"]:
        return prev["direction"]

    # =========================
    # 3. MICRO REVERSIÓN
    # =========================
    if prev["direction"] != prev2["direction"]:
        return last["direction"]

    # =========================
    # 4. RUPTURA SIMPLE
    # =========================
    if last["close"] > prev["high"]:
        return "call"

    if last["close"] < prev["low"]:
        return "put"

    return None


# =========================
# SCORE SUAVE (NO BLOQUEA)
# =========================
def score_pair(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    score = 0

    if last["direction"] == prev["direction"]:
        score += 1

    if prev["direction"] == prev2["direction"]:
        score += 1

    if last["range"] > prev["range"] * 0.7:
        score += 1

    return score
