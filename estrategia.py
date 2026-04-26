import pandas as pd

def calculate_indicators(df):
    return df  # 🔥 sin indicadores


def check_signal(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    body = abs(last["close"] - last["open"])
    wick_up = last["high"] - max(last["close"], last["open"])
    wick_down = min(last["close"], last["open"]) - last["low"]

    # ===============================
    # 🔴 REVERSIÓN VENTA (rechazo arriba)
    # ===============================
    if wick_up > body * 2 and last["close"] < last["open"]:
        return "put"

    # ===============================
    # 🔵 REVERSIÓN COMPRA (rechazo abajo)
    # ===============================
    if wick_down > body * 2 and last["close"] > last["open"]:
        return "call"

    # ===============================
    # 🚀 CONTINUIDAD COMPRA (breakout)
    # ===============================
    if last["close"] > prev["high"]:
        return "call"

    # ===============================
    # 🚀 CONTINUIDAD VENTA
    # ===============================
    if last["close"] < prev["low"]:
        return "put"

    return None


def score_pair(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    score = 0

    if last["close"] > prev["high"]:
        score += 2

    if last["close"] < prev["low"]:
        score += 2

    body = abs(last["close"] - last["open"])
    if body > (last["high"] - last["low"]) * 0.6:
        score += 1

    return score
