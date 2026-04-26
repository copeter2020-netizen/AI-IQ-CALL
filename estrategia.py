import pandas as pd
import numpy as np

def calculate_indicators(df):

    df['ema200'] = df['close'].ewm(span=200).mean()
    df['ema_slope'] = df['ema200'].diff()

    period = 20
    df['ma'] = df['close'].rolling(period).mean()
    df['diff'] = df['close'] - df['ma']

    df['pos'] = df['diff'].clip(lower=0)
    df['neg'] = (-df['diff']).clip(lower=0)

    df['sum_pos'] = df['pos'].rolling(period).sum()
    df['sum_neg'] = df['neg'].rolling(period).sum()

    df['tii'] = 100 * (df['sum_pos'] / (df['sum_pos'] + df['sum_neg'] + 1e-9))

    df['tr'] = np.maximum(df['high'] - df['low'],
                 np.maximum(abs(df['high'] - df['close'].shift()),
                            abs(df['low'] - df['close'].shift())))
    df['atr'] = df['tr'].rolling(14).mean()

    return df


def check_signal(df):

    if len(df) < 220:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # volatilidad
    if last['atr'] < df['atr'].mean():
        return None

    # fuerza vela
    body = abs(last['close'] - last['open'])
    rng = last['high'] - last['low']
    if rng == 0 or body / rng < 0.55:
        return None

    trend_up = last['close'] > last['ema200'] and last['ema_slope'] > 0
    trend_down = last['close'] < last['ema200'] and last['ema_slope'] < 0

    tii_up = prev['tii'] < 25 and last['tii'] > 25
    tii_down = prev['tii'] > 75 and last['tii'] < 75

    breakout_buy = last['close'] > prev['high']
    breakout_sell = last['close'] < prev['low']

    if trend_up and tii_up and breakout_buy:
        return "call"

    if trend_down and tii_down and breakout_sell:
        return "put"

    return None


def score_pair(df):

    score = 0
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if last['close'] > last['ema200'] or last['close'] < last['ema200']:
        score += 1

    if prev['tii'] < 25 and last['tii'] > 25:
        score += 1
    if prev['tii'] > 75 and last['tii'] < 75:
        score += 1

    body = abs(last['close'] - last['open'])
    rng = last['high'] - last['low']

    if rng > 0 and body / rng > 0.6:
        score += 1

    if last['atr'] > df['atr'].mean():
        score += 1

    return score
