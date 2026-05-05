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

# ================= LIQUIDEZ FLEXIBLE =================

def liquidity_sweep(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # trampa alcista (más flexible)
    if last["high"] > prev["high"]:
        if last["close"] < last["high"]:
            return "bearish"

    # trampa bajista
    if last["low"] < prev["low"]:
        if last["close"] > last["low"]:
            return "bullish"

    return None

# ================= SEÑAL PRINCIPAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None, None

    # tendencia real M5
    trend_up = df_m5["ema20"].iloc[-1] > df_m5["ema50"].iloc[-1]
    trend_down = df_m5["ema20"].iloc[-1] < df_m5["ema50"].iloc[-1]

    # 🔥 detectar sweep en vela anterior
    sweep = liquidity_sweep(df_m1.iloc[:-1])

    if not sweep:
        return None, None

    last = df_m1.iloc[-1]

    # ================= CONFIRMACIÓN =================

    if sweep == "bearish" and trend_down:
        if last["close"] < last["open"]:
            return "put", 2

    if sweep == "bullish" and trend_up:
        if last["close"] > last["open"]:
            return "call", 2

    return None, None
