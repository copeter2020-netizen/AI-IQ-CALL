import pandas as pd

def calculate_indicators(df):
    return df

def is_indecision_candle(candle):
    body = abs(candle["close"] - candle["open"])
    total = candle["high"] - candle["low"]

    if total == 0:
        return True

    # doji o vela débil
    return body < total * 0.2


def check_signal(df):

    last = df.iloc[-2]   # vela cerrada
    prev = df.iloc[-3]

    # ❌ evitar indecisión
    if is_indecision_candle(last):
        return None

    body = abs(last["close"] - last["open"])
    direction = "bull" if last["close"] > last["open"] else "bear"

    # ===============================
    # 🔍 CONTEXTO (últimas 5 velas)
    # ===============================
    recent = df.iloc[-7:-2]

    bullish = sum(1 for i in range(len(recent)) if recent.iloc[i]["close"] > recent.iloc[i]["open"])
    bearish = sum(1 for i in range(len(recent)) if recent.iloc[i]["close"] < recent.iloc[i]["open"])

    # ===============================
    # 🚀 CONTINUIDAD
    # ===============================
    if direction == "bull" and bullish >= 3:
        return "call"

    if direction == "bear" and bearish >= 3:
        return "put"

    # ===============================
    # 🔁 REVERSIÓN (agotamiento)
    # ===============================
    wick_up = last["high"] - max(last["open"], last["close"])
    wick_down = min(last["open"], last["close"]) - last["low"]

    # rechazo abajo → compra
    if wick_down > body * 1.5 and bearish >= 3:
        return "call"

    # rechazo arriba → venta
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

    # 🔥 fuerza de vela
    if body > total * 0.5:
        score += 2

    # 🔥 cierre fuerte
    if last["close"] > prev["close"]:
        score += 1
    if last["close"] < prev["close"]:
        score += 1

    # 🔥 volatilidad suficiente
    if total > (df["high"].iloc[-10:].max() - df["low"].iloc[-10:].min()) * 0.1:
        score += 1

    return score
