import numpy as np

def add_indicators(df):
    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    df["tr"] = np.maximum(df["high"] - df["low"],
                np.maximum(abs(df["high"] - df["close"].shift()),
                           abs(df["low"] - df["close"].shift())))
    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ================= LIQUIDEZ =================

def liquidity_sweep(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # romper máximo previo y cerrar abajo → trampa alcista
    if last["high"] > prev["high"] and last["close"] < prev["high"]:
        return "bearish"

    # romper mínimo previo y cerrar arriba → trampa bajista
    if last["low"] < prev["low"] and last["close"] > prev["low"]:
        return "bullish"

    return None

# ================= CONFIRMACIÓN =================

def confirmation(df, direction):
    last = df.iloc[-1]

    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return False

    strength = body / range_

    if direction == "put":
        return last["close"] < last["open"] and strength > 0.5

    if direction == "call":
        return last["close"] > last["open"] and strength > 0.5

    return False

# ================= SEÑAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60:
        return None, None

    trend_up = df_m5["ema20"].iloc[-1] > df_m5["ema50"].iloc[-1]
    trend_down = df_m5["ema20"].iloc[-1] < df_m5["ema50"].iloc[-1]

    sweep = liquidity_sweep(df_m1)

    if not sweep:
        return None, None

    # 🎯 lógica institucional
    if sweep == "bearish" and trend_down:
        if confirmation(df_m1, "put"):
            return "put", 2

    if sweep == "bullish" and trend_up:
        if confirmation(df_m1, "call"):
            return "call", 2

    return None, None
