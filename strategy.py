import pandas as pd

def body(c):
    return abs(c["close"] - c["open"])

def candle_range(c):
    return c["max"] - c["min"]

def is_bullish(c):
    return c["close"] > c["open"]

def is_bearish(c):
    return c["close"] < c["open"]

def fuerza(c):
    r = candle_range(c)
    if r == 0:
        return 0
    return body(c) / r

def ema(df, period=20):
    return df["close"].ewm(span=period).mean()

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def soporte_resistencia(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia

def tendencia_alcista(df):
    ultimas = df.tail(6)
    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))
    return verdes >= 3

def impulso_alcista(df):
    return is_bullish(df.iloc[-1])

def confirmacion_alcista(c):
    return fuerza(c) > 0.5  # 🔥 más estricta

# ==========================
# FILTRO VELA LIMPIA (NUEVO)
# ==========================
def vela_valida(c):

    r = candle_range(c)
    if r == 0:
        return False

    f = fuerza(c)

    upper = c["max"] - max(c["close"], c["open"])
    lower = min(c["close"], c["open"]) - c["min"]

    # ❌ doji / indecisión
    if f < 0.5:
        return False

    # ❌ mechas grandes (rechazo)
    if upper > body(c) * 0.6 or lower > body(c) * 0.6:
        return False

    return True

# ==========================
# EVITAR AGOTAMIENTO (NUEVO)
# ==========================
def evitar_agotamiento(df):

    ultimas = df.tail(3)

    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))

    # ❌ demasiadas velas seguidas (posible retroceso)
    if verdes >= 3:
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

    if impulso_alcista(df):
        score += 1

    if confirmacion_alcista(last):
        score += 1

    if last["close"] > last["ema"]:
        score += 1

    if last["rsi"] > 55:  # 🔥 más fuerte
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

        # 🔥 NUEVOS FILTROS
        if not vela_valida(last):
            return None

        if not evitar_agotamiento(df):
            return None

        score = calcular_score(df, soporte, resistencia)

        # 🔥 entrada más selectiva
        if score >= 5:
            return {
                "action": "call",
                "score": score,
                "maximo": resistencia,
                "minimo": soporte
            }

        return None

    except:
        return None
