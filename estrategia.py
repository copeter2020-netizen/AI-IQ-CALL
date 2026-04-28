# estrategia.py

# =========================================
# NO usamos indicadores clásicos
# Solo acción del precio (price action)
# =========================================

def calculate_indicators(data):
    # Se devuelve la data tal cual (compatibilidad con bot)
    return data


# =========================================
# DETECCIÓN DE SEÑAL (CONTINUIDAD)
# =========================================
def check_signal(data):

    # seguridad
    if len(data) < 3:
        return None

    last = data[-1]
    prev = data[-2]

    open_ = last["open"]
    close = last["close"]
    high = last["high"]
    low = last["low"]

    # =========================
    # CALCULO FUERZA DE VELA
    # =========================
    body = abs(close - open_)
    rango = high - low

    if rango == 0:
        return None

    fuerza = body / rango

    # ❌ evitar indecisión / doji
    if fuerza < 0.55:
        return None

    # =========================
    # CONTINUIDAD ALCISTA
    # =========================
    if close > open_ and close > prev["close"]:
        return "call"

    # =========================
    # CONTINUIDAD BAJISTA
    # =========================
    if close < open_ and close < prev["close"]:
        return "put"

    return None


# =========================================
# SCORE (PRIORIZA MEJOR PAR)
# =========================================
def score_pair(data):

    if len(data) < 4:
        return 0

    last = data[-1]
    prev = data[-2]

    score = 0

    # =========================
    # FUERZA DE VELA
    # =========================
    body = abs(last["close"] - last["open"])
    rango = last["high"] - last["low"]

    if rango > 0:
        fuerza = body / rango

        if fuerza > 0.7:
            score += 3
        elif fuerza > 0.6:
            score += 2

    # =========================
    # CONTINUIDAD ESTRUCTURA
    # =========================
    if last["close"] > prev["close"]:
        score += 2

    if last["close"] < prev["close"]:
        score += 2

    return score
