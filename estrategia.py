import numpy as np

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    # ATR
    df["tr"] = np.maximum(df["high"] - df["low"],
                np.maximum(abs(df["high"] - df["close"].shift()),
                           abs(df["low"] - df["close"].shift())))
    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ================= FILTRO PRO =================

def high_quality_entry(df_m1, df_m5):

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    prev2 = df_m1.iloc[-3]

    # ================= TENDENCIA M5 =================
    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    # evitar mercado plano
    if abs(ema20 - ema50) < 0.00005:
        return None

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    # ================= ANTI LATERAL =================
    if df_m1["atr"].iloc[-1] < df_m1["atr"].mean():
        return None

    # ================= VELA FUERTE =================
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return None

    strength = body / range_

    if strength < 0.75:
        return None

    # ================= EVITAR ENTRADA TARDE =================
    if (prev["close"] > prev2["close"] and last["close"] > prev["close"]) or \
       (prev["close"] < prev2["close"] and last["close"] < prev["close"]):
        return None

    # ================= RUPTURA REAL =================
    breakout_up = last["close"] > prev["high"]
    breakout_down = last["close"] < prev["low"]

    if trend_up and breakout_up:
        return "call"

    if trend_down and breakout_down:
        return "put"

    return None
