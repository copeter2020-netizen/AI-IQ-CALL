import pandas as pd

# ================= CONFIG =================

TOL = 0.0003
MIN_BODY = 0.00025
MIN_WIDTH = 0.0006

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma

    df['bb_width'] = df['upper_band'] - df['lower_band']

    # pendiente de EMA (fuerza de tendencia)
    df['ema_slope'] = df['ema_100'].diff()

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 50:
        return False

    c = df.iloc[-2]  # vela cerrada

    trend = c['close'] < c['ema_100'] and c['ema_slope'] < 0
    volatility = c['bb_width'] > MIN_WIDTH

    body = abs(c['close'] - c['open'])
    strong = body > MIN_BODY

    cross = (
        c['lower_band'] > c['ema_100'] or
        abs(c['lower_band'] - c['ema_100']) < TOL or
        c['low'] < c['ema_100']
    )

    mid_break = c['close'] > c['mid_band']
    red = c['close'] < c['open']

    if pair:
        print(f"\n📊 {pair} BUY")
        print("trend:", trend)
        print("volatility:", volatility)
        print("strong:", strong)
        print("cross:", cross)
        print("mid:", mid_break)

    return trend and volatility and strong and cross and mid_break and red


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 50:
        return False

    c = df.iloc[-2]

    trend = c['close'] > c['ema_100'] and c['ema_slope'] > 0
    volatility = c['bb_width'] > MIN_WIDTH

    body = abs(c['close'] - c['open'])
    strong = body > MIN_BODY

    cross = (
        c['upper_band'] < c['ema_100'] or
        abs(c['upper_band'] - c['ema_100']) < TOL or
        c['high'] > c['ema_100']
    )

    mid_break = c['close'] < c['mid_band']
    green = c['close'] > c['open']

    if pair:
        print(f"\n📊 {pair} SELL")
        print("trend:", trend)
        print("volatility:", volatility)
        print("strong:", strong)
        print("cross:", cross)
        print("mid:", mid_break)

    return trend and volatility and strong and cross and mid_break and green
