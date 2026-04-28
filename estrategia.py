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
# SEÑAL FLEXIBLE (OPERA MÁS)
# =========================
def check_signal(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    # ❌ eliminar solo doji extremo
    if last["body"] < last["range"] * 0.1:
        return None

    # =========================
    # CONTINUIDAD SIMPLE
    # =========================
    if last["direction"] == prev["direction"]:
        return last["direction"]

    # =========================
    # REVERSIÓN SIMPLE
    # =========================
    if prev["direction"] != prev2["direction"]:
        return last["direction"]

    return None


# =========================
# SCORE SUAVE
# =========================
def score_pair(data):

    last = data[-1]
    prev = data[-2]
    prev2 = data[-3]

    score = 0

    # continuidad
    if last["direction"] == prev["direction"]:
        score += 1

    # reversión
    if prev["direction"] != prev2["direction"]:
        score += 1

    # movimiento real
    if last["range"] > prev["range"] * 0.8:
        score += 1

    return score
