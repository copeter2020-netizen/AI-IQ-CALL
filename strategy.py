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


def is_bearish(c):
    return c["close"] < c["open"]


# ==========================
# RANGO
# ==========================
def rango_alto(df):
    return df["max"].rolling(15).max().iloc[-1]


def rango_bajo(df):
    return df["min"].rolling(15).min().iloc[-1]


def es_rango(df):
    alto = rango_alto(df)
    bajo = rango_bajo(df)
    rango = alto - bajo

    return rango < (df["close"].iloc[-1] * 0.003)


# ==========================
# RECHAZOS
# ==========================
def rechazo_inferior(c):
    lower = min(c["close"], c["open"]) - c["min"]
    return lower > body(c) * 1.2


def rechazo_superior(c):
    upper = c["max"] - max(c["close"], c["open"])
    return upper > body(c) * 1.2


# ==========================
# NIVELES
# ==========================
def cerca_soporte(c, soporte):
    return abs(c["min"] - soporte) < (soporte * 0.0015)


def cerca_resistencia(c, resistencia):
    return abs(c["max"] - resistencia) < (resistencia * 0.0015)


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 30:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]
        prev2 = df.iloc[-3]

        if not es_rango(df):
            return None

        resistencia = rango_alto(df)
        soporte = rango_bajo(df)

        # ==========================
        # CALL
        # ==========================
        if (
            cerca_soporte(prev, soporte)
            and rechazo_inferior(prev)
            and is_bullish(prev)
            and fuerza(prev) > 0.4
            and prev["close"] > prev2["close"]
            and is_bullish(last)
            and fuerza(last) > 0.4
        ):
            return {"action": "call", "score": 10}

        # ==========================
        # PUT
        # ==========================
        if (
            cerca_resistencia(prev, resistencia)
            and rechazo_superior(prev)
            and is_bearish(prev)
            and fuerza(prev) > 0.4
            and prev["close"] < prev2["close"]
            and is_bearish(last)
            and fuerza(last) > 0.4
        ):
            return {"action": "put", "score": 10}

        return None

    except:
        return None
