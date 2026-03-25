import pandas as pd


def ema(values, period):
    return pd.Series(values).ewm(span=period).mean().tolist()


def fuerza(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    if rango == 0:
        return 0
    return cuerpo / rango


def is_bullish(c):
    return c["close"] > c["open"]


def is_bearish(c):
    return c["close"] < c["open"]


def liquidity_sweep_high(prev, last):
    return last["max"] > prev["max"] and last["close"] < prev["max"]


def liquidity_sweep_low(prev, last):
    return last["min"] < prev["min"] and last["close"] > prev["min"]


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 30:
            return None

        closes = [c["close"] for c in candles]

        ema20 = ema(closes, 20)
        ema8 = ema(closes, 8)

        last = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3]

        alcista = ema8[-1] > ema20[-1]
        bajista = ema8[-1] < ema20[-1]

        # ==========================
        # HEDGE FUND BUY (CALL)
        # ==========================
        if alcista:

            if (
                liquidity_sweep_low(prev, last) and
                is_bullish(last) and
                fuerza(last) > 0.5 and
                last["close"] > prev["open"]
            ):
                return {
                    "action": "call",
                    "score": 6,
                    "tipo": "liquidity_buy"
                }

        # ==========================
        # HEDGE FUND SELL (PUT)
        # ==========================
        if bajista:

            if (
                liquidity_sweep_high(prev, last) and
                is_bearish(last) and
                fuerza(last) > 0.5 and
                last["close"] < prev["open"]
            ):
                return {
                    "action": "put",
                    "score": 6,
                    "tipo": "liquidity_sell"
                }

        return None

    except:
        return None
