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

# ================= FILTROS =================

def strong_sr_zone(df):
    if len(df) < 60:
        return True

    high = df["high"].rolling(50).max().iloc[-2]
    low = df["low"].rolling(50).min().iloc[-2]
    price = df["close"].iloc[-1]
    atr = df["atr"].iloc[-1]

    return abs(price - high) < atr or abs(price - low) < atr


def is_overextended(df):
    move = abs(df["close"].iloc[-1] - df["close"].iloc[-7])
    atr = df["atr"].iloc[-1]

    return move > atr * 2.5


def too_many_candles(df):
    last3 = df.iloc[-3:]
    bulls = all(c["close"] > c["open"] for _, c in last3.iterrows())
    bears = all(c["close"] < c["open"] for _, c in last3.iterrows())
    return bulls or bears


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


def is_fake_breakout(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return True

    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return True

    return False

# ================= SEÑAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]

    # ❌ filtros duros
    if strong_sr_zone(df_m1):
        return None

    if is_overextended(df_m1):
        return None

    if too_many_candles(df_m1):
        return None

    if is_fake_breakout(df_m1):
        return None

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

    # 🔥 fuerza
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return None

    if (body / range_) < 0.7:
        return None

    # ================= CALL =================
    if (
        trend_up and
        last["close"] > prev["high"] and
        rejection != "down"
    ):
        return "call"

    # ================= PUT =================
    if (
        trend_down and
        last["close"] < prev["low"] and
        rejection != "up"
    ):
        return "put"

    return None
