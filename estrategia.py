import pandas as pd

# ================= CONFIG =================

# 🔥 tolerancia para detectar cruce (ajustada para OTC)
TOLERANCE = 0.0005


# ================= INDICADORES =================

def calculate_indicators(df):
    # EMA 100
    df['ema_100'] = df['close'].ewm(span=100).mean()

    # Bollinger Bands
    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 20:
        return False

    prev = df.iloc[-3]
    signal = df.iloc[-2]

    # 🔥 CRUCE FLEXIBLE (SOLUCIÓN REAL)
    cross = (
        abs(prev['lower_band'] - prev['ema_100']) < TOLERANCE or
        abs(signal['lower_band'] - signal['ema_100']) < TOLERANCE or
        signal['lower_band'] > signal['ema_100']
    )

    # 🔥 RUPTURA REAL (evita falsas entradas)
    breakout = (
        signal['close'] > signal['mid_band'] and
        (signal['close'] - signal['mid_band']) > (TOLERANCE / 2)
    )

    # ================= DEBUG =================

    if pair:
        print(f"\n📊 {pair} BUY")
        print(f"Lower prev: {prev['lower_band']:.5f} | EMA prev: {prev['ema_100']:.5f}")
        print(f"Lower now: {signal['lower_band']:.5f} | EMA now: {signal['ema_100']:.5f}")
        print(f"Close: {signal['close']:.5f} | Mid: {signal['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 20:
        return False

    prev = df.iloc[-3]
    signal = df.iloc[-2]

    # 🔥 CRUCE FLEXIBLE
    cross = (
        abs(prev['upper_band'] - prev['ema_100']) < TOLERANCE or
        abs(signal['upper_band'] - signal['ema_100']) < TOLERANCE or
        signal['upper_band'] < signal['ema_100']
    )

    # 🔥 RUPTURA REAL
    breakout = (
        signal['close'] < signal['mid_band'] and
        (signal['mid_band'] - signal['close']) > (TOLERANCE / 2)
    )

    # ================= DEBUG =================

    if pair:
        print(f"\n📊 {pair} SELL")
        print(f"Upper prev: {prev['upper_band']:.5f} | EMA prev: {prev['ema_100']:.5f}")
        print(f"Upper now: {signal['upper_band']:.5f} | EMA now: {signal['ema_100']:.5f}")
        print(f"Close: {signal['close']:.5f} | Mid: {signal['mid_band']:.5f}")
        print("CRUCE:", cross)
        print("BREAK:", breakout)

    return cross and breakout
