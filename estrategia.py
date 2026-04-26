import pandas as pd

# ================= PARÁMETROS =================
EMA_PERIOD = 200
TII_PERIOD = 30
SWING_LOOKBACK = 5
RANGE_LOOKBACK = 20

TOL = 0.00015
MIN_BODY = 0.00012

# ================= INDICADORES =================
def calculate_indicators(df):
    close = df["close"]

    # EMA tendencia
    df["ema"] = close.ewm(span=EMA_PERIOD).mean()

    # TII
    ma = close.rolling(TII_PERIOD).mean()
    diff = close - ma
    pos = diff.clip(lower=0)
    neg = (-diff).clip(lower=0)
    sum_pos = pos.rolling(TII_PERIOD).sum()
    sum_neg = neg.rolling(TII_PERIOD).sum()
    df["tii"] = 100 * (sum_pos / (sum_pos + sum_neg + 1e-9))

    # swings (estructura)
    df["swing_high"] = df["high"].rolling(SWING_LOOKBACK).max()
    df["swing_low"] = df["low"].rolling(SWING_LOOKBACK).min()

    return df


# ================= LÓGICA INSTITUCIONAL =================
def check_signal(df):
    if len(df) < 210:
        return None

    c = df.iloc[-2]  # vela cerrada
    p = df.iloc[-3]

    # ----------------------------
    # 🧠 CONTEXTO
    # ----------------------------
    trend_up = c["close"] > c["ema"]
    trend_down = c["close"] < c["ema"]

    body = abs(c["close"] - c["open"])
    if body < MIN_BODY:
        return None

    # ----------------------------
    # 🔍 LIQUIDEZ (igual highs/lows)
    # ----------------------------
    recent_high = df["high"].iloc[-RANGE_LOOKBACK:].max()
    recent_low = df["low"].iloc[-RANGE_LOOKBACK:].min()

    equal_highs = abs(c["high"] - recent_high) < TOL
    equal_lows = abs(c["low"] - recent_low) < TOL

    # ----------------------------
    # 🧲 BARRIDA DE LIQUIDEZ (fake breakout)
    # ----------------------------
    sweep_high = c["high"] > recent_high and c["close"] < recent_high
    sweep_low = c["low"] < recent_low and c["close"] > recent_low

    # ----------------------------
    # ⚡ CONFIRMACIÓN (micro estructura)
    # ----------------------------
    break_down = c["close"] < p["low"]
    break_up = c["close"] > p["high"]

    # ----------------------------
    # 🎯 TII timing
    # ----------------------------
    tii_buy = p["tii"] < 30 and c["tii"] > 30
    tii_sell = p["tii"] > 70 and c["tii"] < 70

    # ============================
    # 🟢 CALL (liquidity grab abajo)
    # ============================
    if (
        trend_up and
        (equal_lows or sweep_low) and
        tii_buy and
        break_up
    ):
        return "call"

    # ============================
    # 🔴 PUT (liquidity grab arriba)
    # ============================
    if (
        trend_down and
        (equal_highs or sweep_high) and
        tii_sell and
        break_down
    ):
        return "put"

    return None
