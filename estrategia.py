import pandas as pd

# ================= INDICADORES =================

def calculate(df):
    df['ema50'] = df['close'].ewm(span=50).mean()

    # fuerza de vela
    df['body'] = abs(df['close'] - df['open'])

    # volatilidad simple
    df['volatility'] = df['high'] - df['low']

    return df


# ================= SCORE =================

def evaluate_pair(df):
    df = calculate(df)

    if len(df) < 60:
        return None

    c = df.iloc[-2]  # vela cerrada

    score = 0
    direction = None

    # 🔥 TENDENCIA
    if c['close'] > c['ema50']:
        direction = "call"
        score += 1
    elif c['close'] < c['ema50']:
        direction = "put"
        score += 1

    # 🔥 PULLBACK (precio cerca EMA)
    if abs(c['close'] - c['ema50']) < 0.0005:
        score += 1

    # 🔥 FUERZA
    if c['body'] > 0.0003:
        score += 1

    # 🔥 VOLATILIDAD
    if c['volatility'] > 0.0006:
        score += 1

    return {
        "score": score,
        "direction": direction
    }
