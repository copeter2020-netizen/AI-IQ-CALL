import numpy as np

# ================= INDICADORES =================

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    df["tr"] = np.maximum(df["high"] - df["low"],
                np.maximum(abs(df["high"] - df["close"].shift()),
                           abs(df["low"] - df["close"].shift())))
    df["atr"] = df["tr"].rolling(14).mean()

    # CCI
    tp = (df["high"] + df["low"] + df["close"]) / 3
    sma = tp.rolling(20).mean()
    mad = (tp - sma).abs().rolling(20).mean()
    df["cci"] = (tp - sma) / (0.015 * mad)

    return df

# ================= SOPORTE FUERTE =================

def strong_support_resistance(df):
    if len(df) < 40:
        return True

    last = df.iloc[-1]
    atr = df["atr"].iloc[-1]

    high_zone = df["high"].rolling(30).max().iloc[-2]
    low_zone = df["low"].rolling(30).min().iloc[-2]

    if abs(last["close"] - high_zone) < atr:
        return True

    if abs(last["close"] - low_zone) < atr:
        return True

    return False

# ================= SOBREEXTENSION =================

def is_overextended(df):
    if len(df) < 10:
        return True

    last = df.iloc[-1]
    move = abs(last["close"] - df["close"].iloc[-5])
    atr = df["atr"].iloc[-1]

    return move > atr * 2

# ================= VELAS CONSECUTIVAS =================

def too_many_same_candles(df):
    last3 = df.iloc[-3:]

    bulls = all(c["close"] > c["open"] for _, c in last3.iterrows())
    bears = all(c["close"] < c["open"] for _, c in last3.iterrows())

    return bulls or bears

# ================= RECHAZO =================

def has_rejection(df):
    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    upper = last["high"] - max(last["close"], last["open"])
    lower = min(last["close"], last["open"]) - last["low"]

    if upper > body * 1.5:
        return "down"

    if lower > body * 1.5:
        return "up"

    return None

# ================= FAKE BREAKOUT =================

def is_fake_breakout(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False

# ================= FILTRO CCI =================

def cci_filter(df, direction):
    cci = df["cci"].iloc[-1]

    if direction == "call" and cci > 100:
        return False

    if direction == "put" and cci < -100:
        return False

    return True

# ================= SEÑAL PRO =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 50 or len(df_m5) < 50:
        return None

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]
    prev2 = df_m1.iloc[-3]

    # 🔥 FILTROS DUROS
    if strong_support_resistance(df_m1):
        return None

    if is_overextended(df_m1):
        return None

    if too_many_same_candles(df_m1):
        return None

    if is_fake_breakout(df_m1):
        return None

    rejection = has_rejection(df_m1)

    # 🔥 TENDENCIA M5
    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    if abs(ema20 - ema50) < 0.00005:
        return None

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    # 🔥 ATR
    if df_m1["atr"].iloc[-1] < df_m1["atr"].mean():
        return None

    # 🔥 FUERZA
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return None

    if (body / range_) < 0.7:
        return None

    # ❌ evitar entrada tarde
    if (prev["close"] > prev2["close"] and last["close"] > prev["close"]) or \
       (prev["close"] < prev2["close"] and last["close"] < prev["close"]):
        return None

    # ================= CALL =================
    if trend_up and last["close"] > prev["high"] and rejection != "down":
        if cci_filter(df_m1, "call"):
            return "call"

    # ================= PUT =================
    if trend_down and last["close"] < prev["low"] and rejection != "up":
        if cci_filter(df_m1, "put"):
            return "put"

    return None
