import pandas as pd

def calculate_indicators(df):
    return df  # sin indicadores


def check_signal(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    # breakout
    if last["close"] > prev["high"]:
        return "call"

    if last["close"] < prev["low"]:
        return "put"

    # reversión
    body = abs(last["close"] - last["open"])
    wick_up = last["high"] - max(last["open"], last["close"])
    wick_down = min(last["open"], last["close"]) - last["low"]

    if wick_down > body * 2:
        return "call"

    if wick_up > body * 2:
        return "put"

    return None


def score_pair(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    score = 0

    body = abs(last["close"] - last["open"])
    range_candle = last["high"] - last["low"]

    # 🔥 fuerza de vela
    if body > range_candle * 0.6:
        score += 1

    # 🔥 breakout real
    if last["close"] > prev["high"]:
        score += 2

    if last["close"] < prev["low"]:
        score += 2

    # 🔥 continuidad
    if last["close"] > prev["close"]:
        score += 1

    if last["close"] < prev["close"]:
        score += 1

    # ❌ rango (castigo)
    if range_candle < (df["high"].iloc[-10:].max() - df["low"].iloc[-10:].min()) * 0.2:
        score -= 1

    return score
