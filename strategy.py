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
# TENDENCIA BAJISTA
# ==========================
def tendencia_bajista(df):
    ultimas = df.tail(6)
    rojas = sum(1 for i in range(len(ultimas)) if is_bearish(ultimas.iloc[i]))
    return rojas >= 3

# ==========================
# CONTINUIDAD BAJISTA
# ==========================
def continuidad_bajista(df):
    c1 = df.iloc[-1]
    c2 = df.iloc[-2]

    if not is_bearish(c1):
        return False

    if fuerza(c1) < 0.5:
        return False

    # rompe mínimo anterior
    if c1["close"] >= c2["min"]:
        return False

    return True

# ==========================
# EVITAR INDECISIÓN
# ==========================
def vela_limpia(c):
    r = candle_range(c)
    if r == 0:
        return False

    f = fuerza(c)

    upper = c["max"] - max(c["close"], c["open"])
    lower = min(c["close"], c["open"]) - c["min"]

    if f < 0.5:
        return False

    if upper > body(c) * 0.6 or lower > body(c) * 0.6:
        return False

    return True

# ==========================
# SCORE INTELIGENTE
# ==========================
def calcular_score(df, soporte, resistencia):

    last = df.iloc[-1]
    score = 0

    if tendencia_alcista(df):
        score += 2

    if is_bullish(last):
        score += 1

    if fuerza(last) > 0.4:
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

        last = df.iloc[-1]

        # ==========================
        # 🔼 ALCISTA (tu lógica original)
        # ==========================
        if tendencia_alcista(df):

            score = calcular_score(df, soporte, resistencia)

            if score >= 4 and vela_limpia(last):
                return {
                    "action": "call",
                    "score": score,
                    "maximo": resistencia,
                    "minimo": soporte
                }

        # ==========================
        # 🔽 BAJISTA (nuevo)
        # ==========================
        if tendencia_bajista(df):

            if not continuidad_bajista(df):
                return None

            if not vela_limpia(last):
                return None

            # evitar soporte (rebote)
            if last["close"] <= soporte:
                return None

            if last["close"] > last["ema"]:
                return None

            if last["rsi"] > 50:
                return None

            score = fuerza(last)

            return {
                "action": "put",
                "score": score,
                "maximo": resistencia,
                "minimo": soporte
            }

        return None

    except:
        return None
