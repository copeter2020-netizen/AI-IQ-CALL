import pandas as pd

def calculate_indicators(df):
    return df

def is_indecision(c):
    body = abs(c["close"] - c["open"])
    total = c["high"] - c["low"]

    if total == 0:
        return True

    return body < total * 0.25


def trend(df):
    data = df.iloc[-10:-2]

    up = sum(1 for i in range(len(data)) if data.iloc[i]["close"] > data.iloc[i]["open"])
    down = sum(1 for i in range(len(data)) if data.iloc[i]["close"] < data.iloc[i]["open"])

    if up > down:
        return "bull"
    elif down > up:
        return "bear"
    return "range"


def check_signal(df):

    last = df.iloc[-2]
    prev = df.iloc[-3]

    if is_indecision(last):
        return None

    t = trend(df)

    body = abs(last["close"] - last["open"])
    total = last["high"] - last["low"]

    # CONTINUIDAD
    if t == "bull":
        if last["close"] > prev["high"] and body > total * 0.5:
            return "call"

    if t == "bear":
        if last["close"] < prev["low"] and body > total * 0.5:
            return "put"

    # REVERSIÓN
    wick_up = last["high"] - max(last["open"], last["close"])
    wick_down = min(last["open"], last["close"]) - last["low"]

    if t == "bear" and wick_down > body * 1.5:
        return "call"

    if t == "bull" and wick_up > body * 1.5:
        return "put"

    return None


def score_pair(df):

    last = df.iloc[-2]
    total = last["high"] - last["low"]
    body = abs(last["close"] - last["open"])

    if total == 0:
        return 0

    score = 0

    if body > total * 0.5:
        score += 2

    if last["close"] > last["open"]:
        score += 1
    else:
        score += 1

    return score
