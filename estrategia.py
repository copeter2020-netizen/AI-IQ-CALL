import pandas as pd

# ================= CONFIG =================

TOL = 0.0003
MIN_BODY = 0.0002
MIN_WIDTH = 0.0005

# ================= INDICADORES =================

def calculate_indicators(df):
    df['ema_100'] = df['close'].ewm(span=100).mean()
    df['ema_50'] = df['close'].ewm(span=50).mean()

    ma = df['close'].rolling(14).mean()
    std = df['close'].rolling(14).std()

    df['upper_band'] = ma + 2 * std
    df['lower_band'] = ma - 2 * std
    df['mid_band'] = ma

    df['bb_width'] = df['upper_band'] - df['lower_band']
    df['ema_slope'] = df['ema_100'].diff()

    return df


# ================= BUY =================

def check_buy_signal(df, pair=None):
    if len(df) < 50:
        return False

    c = df.iloc[-2]

    # 🔥 tendencia bajista pero perdiendo fuerza (rebote)
    trend = c['ema_slope'] < 0

    # 🔥 zona de soporte dinámico
    pullback = c['low'] <= c['ema_100'] * (1 + TOL)

    # 🔥 recuperación
    close_back = c['close'] > c['ema_50']

    # 🔥 fuerza mínima de vela
    body = abs(c['close'] - c['open'])
    strong = body > MIN_BODY

    # 🔥 volatilidad mínima
    volatility = c['bb_width'] > MIN_WIDTH

    return trend and pullback and close_back and strong and volatility


# ================= SELL =================

def check_sell_signal(df, pair=None):
    if len(df) < 50:
        return False

    c = df.iloc[-2]

    # 🔥 tendencia alcista perdiendo fuerza
    trend = c['ema_slope'] > 0

    # 🔥 rechazo de zona EMA
    pullback = c['high'] >= c['ema_100'] * (1 - TOL)

    # 🔥 confirmación bajista
    close_back = c['close'] < c['ema_50']

    body = abs(c['close'] - c['open'])
    strong = body > MIN_BODY

    volatility = c['bb_width'] > MIN_WIDTH

    return trend and pullback and close_back and strong and volatility
