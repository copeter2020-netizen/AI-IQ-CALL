import pandas as pd

def calculate_indicators(df):
    return df

def is_indecision(c):
    body = abs(c["close"] - c["open"])
    total = c["high"] - c["low"]

    if total == 0:
        return True

    return body < total * 0.2  # doji o débil


def check_signal(df):

    last = df.iloc[-2]   # vela cerrada
    prev = df.iloc[-3]

    # ❌ evitar indecisión
    if is_indecision(last):
        return None

    body = abs(last["close"] - last["open"])

    # contexto (últimas velas)
    recent = df.iloc[-7:-2]

    bullish = sum(1 for i in range(len(recent)) if recent.iloc[i]["close"] > recent.iloc[i]["open"])
    bearish = sum(1 for i in range(len(recent)) if recent.iloc[i]["close"] < recent.iloc[i]["open"])

    # ===============================
    # 🚀 CONTINUIDAD
    # ===============================
    if last["close"] > last["open"] and bullish >= 3:
        return "call"

    if last["close"] < last["open"] and bearish >= 3:
        return "put"

    # ===============================
    # 🔁 REVERSIÓN
    # ===============================
    wick_up = last["high"] - max(last["open"], last["close"])
    wick_down = min(last["open"], last["close"]) - last["low"]

    if wick_down > body * 1.5 and bearish >= 3:
        return "call"

    if wick_up > body * 1.5 and bullish >= 3:
        return "put"

    return None


def score_pair(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    body = abs(last["close"] - last["open"])
    total = last["high"] - last["low"]

    if total == 0:
        return 0

    score = 0

    # fuerza de vela
    if body > total * 0.5:
        score += 2

    # continuidad
    if last["close"] > prev["close"]:
        score += 1
    if last["close"] < prev["close"]:
        score += 1

    # volatilidad
    if total > (df["high"].iloc[-10:].max() - df["low"].iloc[-10:].min()) * 0.1:
        score += 1

    return score
