import pandas as pd
import numpy as np

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
# INDICADORES
# ==========================
def ema(df, period=20):
    return df["close"].ewm(span=period).mean()

def rsi(df, period=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==========================
# SOPORTE Y RESISTENCIA
# ==========================
def soporte_resistencia(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia

# ==========================
# TENDENCIA ALCISTA REAL
# ==========================
def tendencia_alcista(df):

    ultimas = df.tail(6)

    verdes = sum(1 for i in range(len(ultimas)) if is_bullish(ultimas.iloc[i]))

    higher_lows = True
    for i in range(1, len(ultimas)):
        if ultimas.iloc[i]["min"] < ultimas.iloc[i-1]["min"]:
            higher_lows = False

    return verdes >= 4 and higher_lows

# ==========================
# IMPULSO ALCISTA
# ==========================
def impulso_alcista(df):
    return (
        is_bullish(df.iloc[-1]) and
        is_bullish(df.iloc[-2])
    )

# ==========================
# CONFIRMACIÓN ALCISTA
# ==========================
def confirmacion_alcista(c):
    f = body(c) / candle_range(c) if candle_range(c) != 0 else 0
    lower = min(c["close"], c["open"]) - c["min"]

    return (
        is_bullish(c)
        and f > 0.5
        and lower < body(c) * 0.5
    )

# ==========================
# PATRONES ALCISTAS
# ==========================
def patron_alcista(df):
    c1 = df.iloc[-1]
    c2 = df.iloc[-2]

    # engulfing alcista
    engulfing = (
        is_bullish(c1) and
        is_bearish(c2) and
        c1["close"] > c2["open"]
    )

    # indecisión (doji)
    doji = body(c1) < candle_range(c1) * 0.2

    return engulfing or doji

# ==========================
# RUPTURA ALCISTA
# ==========================
def ruptura_alcista(df, resistencia):
    return df.iloc[-1]["close"] > resistencia

# ==========================
# FALSO ROMPIMIENTO ALCISTA
# ==========================
def falso_rompimiento(df, resistencia):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    return (
        prev["close"] > resistencia and
        last["close"] < resistencia
    )

# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(c1, c5, c15):

    try:
        df = pd.DataFrame(c1)

        if len(df) < 50:
            return None

        # indicadores
        df["ema"] = ema(df)
        df["rsi"] = rsi(df)

        soporte, resistencia = soporte_resistencia(df)

        last = df.iloc[-1]

        # condiciones
        if not tendencia_alcista(df):
            return None

        if not impulso_alcista(df):
            return None

        if not confirmacion_alcista(last):
            return None

        if not patron_alcista(df):
            return None

        if last["rsi"] < 50:
            return None

        score = 0

        if ruptura_alcista(df, resistencia):
            score += 2

        if not falso_rompimiento(df, resistencia):
            score += 1

        if last["close"] > last["ema"]:
            score += 1

        return {
            "action": "call",
            "score": score,
            "maximo": resistencia,
            "minimo": soporte
        }

    except:
        return None
