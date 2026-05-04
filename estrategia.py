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

# ================= FILTRO REVERSIÓN =================

def momentum_reversal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return False

    strong = (body / range_) > 0.6

    # cambio fuerte de dirección
    if prev["close"] < prev["open"] and last["close"] > last["open"] and strong:
        return True

    if prev["close"] > prev["open"] and last["close"] < last["open"] and strong:
        return True

    return False

# ================= AGOTAMIENTO =================

def trend_exhausted(df):
    count = 0

    for i in range(-1, -7, -1):
        if df["close"].iloc[i] < df["open"].iloc[i]:
            count += 1
        else:
            break

    return count >= 4

# ================= SEÑAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None

    score = 0

    last = df_m1.iloc[-1]
    prev = df_m1.iloc[-2]

    # ❌ BLOQUEOS CLAVE
    if momentum_reversal(df_m1):
        return None

    if trend_exhausted(df_m1):
        return None

    # ================= TENDENCIA M5 =================
    ema20 = df_m5["ema20"].iloc[-1]
    ema50 = df_m5["ema50"].iloc[-1]

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    if abs(ema20 - ema50) > 0.00005:
        score += 1

    # ================= BREAK =================
    if last["close"] > prev["high"]:
        direction = "call"
        score += 2
    elif last["close"] < prev["low"]:
        direction = "put"
        score += 2
    else:
        return None

    # ================= A FAVOR DE TENDENCIA =================
    if (direction == "call" and trend_up) or (direction == "put" and trend_down):
        score += 2

    # ================= FUERZA =================
    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ > 0 and (body / range_) > 0.5:
        score += 1

    # ================= VOLATILIDAD =================
    if df_m1["atr"].iloc[-1] > df_m1["atr"].mean():
        score += 1

    # ================= FILTROS NEGATIVOS =================

    move = abs(df_m1["close"].iloc[-1] - df_m1["close"].iloc[-7])
    if move > df_m1["atr"].iloc[-1] * 2.5:
        score -= 2

    high = df_m1["high"].rolling(50).max().iloc[-2]
    low = df_m1["low"].rolling(50).min().iloc[-2]
    atr = df_m1["atr"].iloc[-1]

    if abs(last["close"] - high) < atr:
        score -= 2

    if abs(last["close"] - low) < atr:
        score -= 2

    # ================= DECISIÓN =================

    if score >= 4:
        return direction

    return None
