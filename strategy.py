import pandas as pd

# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])

def candle_range(c):
    return c["max"] - c["min"]

def is_bullish(c):
    return c["close"] > c["open"]

def is_bearish(c):
    return c["close"] < c["open"]

# ==========================
# FUERZA
# ==========================
def fuerza(c):
    r = candle_range(c)
    if r == 0:
        return 0
    return body(c) / r

# ==========================
# EMA
# ==========================
def ema(df, period=20):
    return df["close"].ewm(span=period).mean()

# ==========================
# RSI
# ==========================
def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================
# SOPORTE / RESISTENCIA
# ==========================
def soporte_resistencia(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia

# ==========================
# TENDENCIA ALCISTA
# ==========================
def tendencia_alcista(df):
    ultimas = df.tail(6)
    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))
    return verdes >= 3

# ==========================
# CONTINUIDAD ALCISTA
# ==========================
def continuidad_alcista(df):

    c1 = df.iloc[-1]
    c2 = df.iloc[-2]

    # debe venir de retroceso
    if not is_bearish(c2):
        return False

    # vela fuerte alcista
    if not is_bullish(c1):
        return False

    if fuerza(c1) < 0.6:
        return False

    # rompe máximo anterior
    if c1["close"] <= c2["max"]:
        return False

    return True

# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(c1, c5, c15):

    try:
        df = pd.DataFrame(c1)

        if len(df) < 30:
            return None

        df["ema"] = ema(df)
        df["rsi"] = rsi(df)

        soporte, resistencia = soporte_resistencia(df)

        last = df.iloc[-1]

        # SOLO TENDENCIA ALCISTA
        if not tendencia_alcista(df):
            return None

        # SOLO CONTINUIDAD
        if not continuidad_alcista(df):
            return None

        # confirmaciones
        if last["close"] < last["ema"]:
            return None

        if last["rsi"] < 55:
            return None

        score = fuerza(last)

        return {
            "action": "call",
            "score": score,
            "maximo": resistencia,
            "minimo": soporte
        }

    except:
        return None
