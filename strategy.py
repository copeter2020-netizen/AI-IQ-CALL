import pandas as pd

def body(c):
    return abs(c["close"] - c["open"])

def candle_range(c):
    return c["max"] - c["min"]

def is_bullish(c):
    return c["close"] > c["open"]

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

def analyze_market(c1, c5, c15):

    try:
        df = pd.DataFrame(c1)

        if len(df) < 30:
            return None

        df["ema"] = ema(df)
        df["rsi"] = rsi(df)

        soporte, resistencia = soporte_resistencia(df)

        last = df.iloc[-1]

        # 🔥 SOLO SI LA VELA CIERRA VERDE
        if not is_bullish(last):
            return None

        score = 0

        if tendencia_alcista(df):
            score += 2

        if fuerza(last) > 0.4:
            score += 1

        if last["close"] > last["ema"]:
            score += 1

        if last["rsi"] > 50:
            score += 1

        if last["close"] > soporte:
            score += 1

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
