import numpy as np

# ================= INDICADORES =================

def add_indicators(df):

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()

    # RSI
    delta = df["close"].diff()

    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, abs(delta), 0)

    avg_gain = (
        np.convolve(gain, np.ones(14)/14, mode='same')
    )

    avg_loss = (
        np.convolve(loss, np.ones(14)/14, mode='same')
    )

    rs = np.where(avg_loss == 0, 0, avg_gain / avg_loss)

    df["rsi"] = 100 - (100 / (1 + rs))

    # ATR
    df["tr"] = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            abs(df["high"] - df["close"].shift()),
            abs(df["low"] - df["close"].shift())
        )
    )

    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ================= TENDENCIA =================

def trend_direction(df_m5):

    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    if ema20 > ema50:
        return "up"

    if ema20 < ema50:
        return "down"

    return None

# ================= IMPULSO =================

def strong_body(candle):

    body = abs(candle["close"] - candle["open"])
    full = candle["high"] - candle["low"]

    if full == 0:
        return False

    return body / full > 0.55

# ================= CONTINUIDAD =================

def continuation_signal(df_m1, direction):

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]

    # CALL
    if direction == "call":

        if (
            last["close"] > last["open"] and
            prev["close"] > prev["open"] and
            last["close"] > prev["close"] and
            strong_body(last)
        ):
            return True

    # PUT
    if direction == "put":

        if (
            last["close"] < last["open"] and
            prev["close"] < prev["open"] and
            last["close"] < prev["close"] and
            strong_body(last)
        ):
            return True

    return False

# ================= FILTRO RSI =================

def rsi_filter(df, direction):

    rsi = df["rsi"].iloc[-1]

    if direction == "call":
        return rsi > 52 and rsi < 75

    if direction == "put":
        return rsi < 48 and rsi > 25

    return False

# ================= FILTRO VOLATILIDAD =================

def volatility_ok(df):

    atr = df["atr"].iloc[-1]
    atr_mean = df["atr"].mean()

    return atr > atr_mean * 0.7

# ================= SEÑAL PRINCIPAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None, None

    if not volatility_ok(df_m1):
        return None, None

    trend = trend_direction(df_m5)

    # ================= CALL =================

    if trend == "up":

        if continuation_signal(df_m1, "call"):

            if rsi_filter(df_m1, "call"):

                return "call", 1

    # ================= PUT =================

    if trend == "down":

        if continuation_signal(df_m1, "put"):

            if rsi_filter(df_m1, "put"):

                return "put", 1

    return None, None
