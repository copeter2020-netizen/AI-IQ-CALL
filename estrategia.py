import pandas as pd

TOL = 0.0003

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
    if len(df) < 20:
        return False

    closed = df.iloc[-2]  # vela cerrada
    live = df.iloc[-1]    # vela en formación

    # 🔥 cruce detectado en vivo
    live_cross = (
        live['lower_band'] > live['ema_100'] or
        abs(live['lower_band'] - live['ema_100']) < TOL or
        live['low'] < live['ema_100']
    )

    # 🔥 confirmación al cierre
    close_cross = closed['lower_band'] > closed['ema_100']

    red = closed['close'] < closed['open']

    mid_break = (
        closed['close'] > closed['mid_band'] or
        closed['high'] > closed['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} BUY")
        print("LIVE:", live_cross)
        print("CLOSE:", close_cross)
        print("ROJA:", red)
        print("MID:", mid_break)

    return live_cross and close_cross and red and mid_break


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 20:
        return False

    closed = df.iloc[-2]
    live = df.iloc[-1]

    live_cross = (
        live['upper_band'] < live['ema_100'] or
        abs(live['upper_band'] - live['ema_100']) < TOL or
        live['high'] > live['ema_100']
    )

    close_cross = closed['upper_band'] < closed['ema_100']

    green = closed['close'] > closed['open']

    mid_break = (
        closed['close'] < closed['mid_band'] or
        closed['low'] < closed['mid_band']
    )

    if pair:
        print(f"\n📊 {pair} SELL")
        print("LIVE:", live_cross)
        print("CLOSE:", close_cross)
        print("VERDE:", green)
        print("MID:", mid_break)

    return live_cross and close_cross and green and mid_break
