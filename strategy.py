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
# RECHAZO (WICK GRANDE)
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
# CONTINUIDAD ALCISTA
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
        prev2 = df.iloc[-3]

        res = resistencia(df)

        # ==========================
        # TENDENCIA ALCISTA
        # ==========================
        if last["close"] < last["ema"]:
            return None

        # ==========================
        # CONTINUIDAD
        # ==========================
        if not continuidad_alcista(df):
            return None

        # ==========================
        # NO INDECISIÓN
        # ==========================
        if es_indecision(last):
            return None

        # ==========================
        # NO RECHAZO
        # ==========================
        if rechazo_superior(last):
            return None

        # ==========================
        # NO AGOTAMIENTO
        # ==========================
        if last["close"] <= prev["close"]:
            return None

        # ==========================
        # NO RESISTENCIA
        # ==========================
        if abs(last["close"] - res) < (res * 0.002):
            return None

        # ==========================
        # CONFIRMACIÓN VELA ANTERIOR
        # ==========================
        if not is_bullish(prev):
            return None

        if fuerza(prev) < 0.5:
            return None

        if rechazo_superior(prev):
            return None

        # ==========================
        # NO RUPTURA / FALSA RUPTURA
        # ==========================
        if last["max"] > prev["max"] and last["close"] < prev["max"]:
            return None

        # ==========================
        # TODO CUMPLE
        # ==========================
        return {
            "action": "call",
            "score": 10
        }

    except:
        return None
