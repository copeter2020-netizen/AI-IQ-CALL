import pandas as pd


# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])


def candle_range(c):
    return c["max"] - c["min"]


def is_bearish(c):
    return c["close"] < c["open"]


# ==========================
# FUERZA REAL
# ==========================
def fuerza(c):
    r = candle_range(c)
    if r == 0:
        return 0
    return body(c) / r


# ==========================
# CONTAR VELAS ROJAS
# ==========================
def contar_rojas(df):
    count = 0
    for i in range(len(df)-1, -1, -1):
        if is_bearish(df.iloc[i]):
            count += 1
        else:
            break
    return count


# ==========================
# TENDENCIA BAJISTA REAL
# ==========================
def tendencia_bajista(df):

    ultimas = df.tail(6)

    rojas = sum(1 for i in range(len(ultimas)) if is_bearish(ultimas.iloc[i]))

    lower_highs = True

    for i in range(1, len(ultimas)):
        if ultimas.iloc[i]["max"] > ultimas.iloc[i-1]["max"]:
            lower_highs = False

    return rojas >= 4 and lower_highs


# ==========================
# IMPULSO BAJISTA
# ==========================
def impulso(df):
    return (
        is_bearish(df.iloc[-1]) and
        is_bearish(df.iloc[-2])
    )


# ==========================
# CONFIRMACIÓN FUERTE
# ==========================
def confirmacion(c):

    f = fuerza(c)

    upper = c["max"] - max(c["close"], c["open"])

    return (
        is_bearish(c)
        and f > 0.5
        and upper < body(c) * 0.5
    )


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(c1, c5, c15):

    try:

        df = pd.DataFrame(c1)

        if len(df) < 25:
            return None

        last = df.iloc[-1]

        # 🔴 BLOQUEOS
        if not tendencia_bajista(df):
            return None

        if not impulso(df):
            return None

        rojas = contar_rojas(df)

        # 🔴 SOLO PRIMERA O SEGUNDA
        if rojas > 2:
            return None

        if not confirmacion(last):
            return None

        score = fuerza(last)

        return {
            "action": "put",
            "score": score
        }

    except:
        return None
