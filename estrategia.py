import pandas as pd

# ================= CONFIG =================

TOLERANCE = 0.0005  # puedes ajustar si operas JPY

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 30:
        return False

    # 🔥 ESTRUCTURA REAL (3 VELAS)
    cross_candle = df.iloc[-4]   # donde ocurre el cruce
    break_candle = df.iloc[-3]   # ruptura confirmada
    entry_candle = df.iloc[-2]   # vela donde se entra

    # ================= CRUCE REAL =================
    cross = (
        (cross_candle['lower_band'] < cross_candle['ema_100'] and
         break_candle['lower_band'] > break_candle['ema_100'])
        or
        abs(break_candle['lower_band'] - break_candle['ema_100']) < TOLERANCE
    )

    # ================= RUPTURA REAL =================
    breakout = (
        break_candle['close'] > break_candle['mid_band'] and
        (break_candle['close'] - break_candle['mid_band']) > (TOLERANCE / 2)
    )

    # ================= DEBUG =================
    if pair:
        print(f"\n📊 {pair} BUY")
        print(f"Cross candle -> Lower: {cross_candle['lower_band']:.5f} | EMA: {cross_candle['ema_100']:.5f}")
        print(f"Break candle -> Lower: {break_candle['lower_band']:.5f} | EMA: {break_candle['ema_100']:.5f}")
        print(f"Break close: {break_candle['close']:.5f} | Mid: {break_candle['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 30:
        return False

    cross_candle = df.iloc[-4]
    break_candle = df.iloc[-3]
    entry_candle = df.iloc[-2]

    # ================= CRUCE REAL =================
    cross = (
        (cross_candle['upper_band'] > cross_candle['ema_100'] and
         break_candle['upper_band'] < break_candle['ema_100'])
        or
        abs(break_candle['upper_band'] - break_candle['ema_100']) < TOLERANCE
    )

    # ================= RUPTURA REAL =================
    breakout = (
        break_candle['close'] < break_candle['mid_band'] and
        (break_candle['mid_band'] - break_candle['close']) > (TOLERANCE / 2)
    )

    # ================= DEBUG =================
    if pair:
        print(f"\n📊 {pair} SELL")
        print(f"Cross candle -> Upper: {cross_candle['upper_band']:.5f} | EMA: {cross_candle['ema_100']:.5f}")
        print(f"Break candle -> Upper: {break_candle['upper_band']:.5f} | EMA: {break_candle['ema_100']:.5f}")
        print(f"Break close: {break_candle['close']:.5f} | Mid: {break_candle['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout
