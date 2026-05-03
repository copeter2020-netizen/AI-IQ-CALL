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

# ================= SOPORTE / RESISTENCIA =================

def is_near_sr(df, tolerance=0.0003):
    last = df.iloc[-1]

    recent_high = df["high"].rolling(20).max().iloc[-2]
    recent_low = df["low"].rolling(20).min().iloc[-2]

    if abs(last["close"] - recent_high) < tolerance:
        return True

    if abs(last["close"] - recent_low) < tolerance:
        return True

    return False

# ================= RECHAZO (MECHAS) =================

def has_rejection(df):
    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    upper_wick = last["high"] - max(last["close"], last["open"])
    lower_wick = min(last["close"], last["open"]) - last["low"]

    if upper_wick > body * 1.5:
        return "down"

    if lower_wick > body * 1.5:
        return "up"

    return None

# ================= ANTI FAKE BREAKOUT =================

def is_fake_breakout(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False

# ================= SEÑAL PRINCIPAL =================

def pro_signal(df_m1, df_m5):

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    prev2 = df_m1.iloc[-3]

    # ❌ evitar rebotes
    if is_near_sr(df_m1):
        return None

    # ❌ evitar manipulación
    if is_fake_breakout(df_m1):
        return None

    # ❌ rechazo
    rejection = has_rejection(df_m1)

    # 🔥 tendencia M5
    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    if abs(ema20 - ema50) < 0.00005:
        return None

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

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

    # ❌ evitar entrada tarde
    if (prev["close"] > prev2["close"] and last["close"] > prev["close"]) or \
       (prev["close"] < prev2["close"] and last["close"] < prev["close"]):
        return None

    # ================= CALL =================
    if (
        trend_up and
        last["close"] > prev["high"] and
        last["close"] > last["open"] and
        rejection != "down"
    ):
        return "call"

    # ================= PUT =================
    if (
        trend_down and
        last["close"] < prev["low"] and
        last["close"] < last["open"] and
        rejection != "up"
    ):
        return "put"

    return None
