import numpy as np

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    df["tr"] = np.maximum(df["high"] - df["low"],
                np.maximum(abs(df["high"] - df["close"].shift()),
                           abs(df["low"] - df["close"].shift())))
    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ================= DETECTOR ANTI MANIPULACION =================

def is_fake_breakout(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # rompió pero cerró dentro → trampa
    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False

# ================= SEÑAL PRO =================

def pro_signal(df_m1, df_m5):

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    prev2 = df_m1.iloc[-3]

    # 🔥 evitar manipulación
    if is_fake_breakout(df_m1):
        return None

    # 🔥 tendencia M5
    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    if abs(ema20 - ema50) < 0.00005:
        return None

    # 🔥 evitar lateral
    if df_m1["atr"].iloc[-1] < df_m1["atr"].mean():
        return None

    # 🔥 fuerza de vela
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return None

    strength = body / range_

    if strength < 0.7:
        return None

    # 🔥 evitar entrar tarde
    if (prev["close"] > prev2["close"] and last["close"] > prev["close"]) or \
       (prev["close"] < prev2["close"] and last["close"] < prev["close"]):
        return None

    # ================= CALL =================
    if (
        trend_up and
        last["close"] > prev["high"] and
        last["close"] > last["open"]
    ):
        return "call"

    # ================= PUT =================
    if (
        trend_down and
        last["close"] < prev["low"] and
        last["close"] < last["open"]
    ):
        return "put"

    return None
