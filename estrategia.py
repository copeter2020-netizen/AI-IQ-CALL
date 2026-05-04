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

def momentum_reversal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    body = abs(last["close"] - last["open"])
    range_ = last["high"] - last["low"]

    if range_ == 0:
        return False

    strong = (body / range_) > 0.6

    if prev["close"] < prev["open"] and last["close"] > last["open"] and strong:
        return True

    if prev["close"] > prev["open"] and last["close"] < last["open"] and strong:
        return True

    return False


def trend_exhausted(df):
    count = 0

    for i in range(-1, -7, -1):
        if df["close"].iloc[i] < df["open"].iloc[i]:
            count += 1
        else:
            break

    return count >= 4

# ================= ENTRADA SNIPER =================

def pullback_entry(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # tendencia
    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    # PUT (tendencia bajista)
    if trend_down:
        pullback = prev["close"] > prev["open"]  # vela verde
        confirm = last["close"] < last["open"] and last["close"] < prev["low"]

        if pullback and confirm:
            return "put"

    # CALL (tendencia alcista)
    if trend_up:
        pullback = prev["close"] < prev["open"]  # vela roja
        confirm = last["close"] > last["open"] and last["close"] > prev["high"]

        if pullback and confirm:
            return "call"

    return None

# ================= SEÑAL FINAL =================

def pro_signal(df_m1, df_m5):

    if len(df_m1) < 60 or len(df_m5) < 60:
        return None

    # ❌ BLOQUEOS
    if momentum_reversal(df_m1):
        return None

    if trend_exhausted(df_m1):
        return None

    # ✅ ENTRADA
    signal = pullback_entry(df_m1)

    return signal
