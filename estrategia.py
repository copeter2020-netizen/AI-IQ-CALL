import pandas as pd

def calculate_indicators(df):
    df["ema"] = df["close"].ewm(span=200).mean()

    ma = df["close"].rolling(30).mean()
    diff = df["close"] - ma

    pos = diff.clip(lower=0)
    neg = (-diff).clip(lower=0)

    df["tii"] = 100 * (pos.rolling(30).sum() /
                       (pos.rolling(30).sum() + neg.rolling(30).sum() + 1e-9))

    return df

def check_signal(df):
    if len(df) < 210:
        return None

    c = df.iloc[-2]
    p = df.iloc[-3]

    trend_up = c["close"] > c["ema"]
    trend_down = c["close"] < c["ema"]

    tii_up = p["tii"] < 30 and c["tii"] > 30
    tii_down = p["tii"] > 70 and c["tii"] < 70

    if trend_up and tii_up and c["close"] > p["high"]:
        return "call"

    if trend_down and tii_down and c["close"] < p["low"]:
        return "put"

    return None
