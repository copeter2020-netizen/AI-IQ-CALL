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
# TENDENCIA ALCISTA (SUAVIZADA)
# ==========================
def tendencia_alcista(df):

    ultimas = df.tail(6)

    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))

    return verdes >= 3

# ==========================
# IMPULSO
# ==========================
def impulso_alcista(df):
    return is_bullish(df.iloc[-1])

# ==========================
# CONFIRMACIÓN
# ==========================
def confirmacion_alcista(c):
    f = fuerza(c)
    return f > 0.4

# ==========================
# SCORE INTELIGENTE
# ==========================
def calcular_score(df, soporte, resistencia):

    last = df.iloc[-1]
    score = 0

    if tendencia_alcista(df):
        score += 2

    if impulso_alcista(df):
        score += 1

    if confirmacion_alcista(last):
        score += 1

    if last["close"] > last["ema"]:
        score += 1

    if last["rsi"] > 50:
        score += 1

    if last["close"] > soporte:
        score += 1

    return score

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

        score = calcular_score(df, soporte, resistencia)

        if score >= 4:
            return {
                "action": "call",
                "score": score,
                "maximo": resistencia,
                "minimo": soporte
            }

        return None

    except:
        return None
