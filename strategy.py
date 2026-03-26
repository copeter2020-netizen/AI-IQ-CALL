import pandas as pd


# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])


def candle_range(c):
    return c["max"] - c["min"]


def fuerza(c):
    r = candle_range(c)
    if r == 0:
        return 0
    return body(c) / r


def is_bullish(c):
    return c["close"] > c["open"]


# ==========================
# EMA
# ==========================
def ema(df, period=20):
    return df["close"].ewm(span=period).mean()


# ==========================
# RESISTENCIA
# ==========================
def resistencia(df):
    return df["max"].rolling(20).max().iloc[-1]


# ==========================
# RECHAZO
# ==========================
def rechazo_superior(c):
    upper = c["max"] - max(c["close"], c["open"])
    return upper > body(c) * 1.2


# ==========================
# INDECISIÓN
# ==========================
def es_indecision(c):
    return fuerza(c) < 0.3


# ==========================
# CONTINUIDAD
# ==========================
def continuidad_alcista(df):
    ultimas = df.tail(4)
    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))
    return verdes >= 3


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 30:
            return None

        df["ema"] = ema(df)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        res = resistencia(df)

        if last["close"] < last["ema"]:
            return None

        if not continuidad_alcista(df):
            return None

        if es_indecision(last):
            return None

        if rechazo_superior(last):
            return None

        if last["close"] <= prev["close"]:
            return None

        if abs(last["close"] - res) < (res * 0.002):
            return None

        if not is_bullish(prev):
            return None

        if fuerza(prev) < 0.5:
            return None

        if rechazo_superior(prev):
            return None

        if last["max"] > prev["max"] and last["close"] < prev["max"]:
            return None

        return {
            "action": "call",
            "score": 10
        }

    except:
        return None
