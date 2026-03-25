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


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 25:
            return None

        closes = [c["close"] for c in candles]

        ema20 = ema(closes, 20)
        ema8 = ema(closes, 8)

        last = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3]

        # ==========================
        # TENDENCIA
        # ==========================
        alcista = ema8[-1] > ema20[-1]
        bajista = ema8[-1] < ema20[-1]

        # ==========================
        # SNIPER BUY (CALL)
        # ==========================
        if alcista:

            # retroceso + continuación
            if (
                is_bearish(prev) and
                is_bullish(last) and
                last["close"] > prev["open"] and
                fuerza(last) > 0.5
            ):

                return {
                    "action": "call",
                    "score": 5,
                    "tipo": "sniper_buy"
                }

        # ==========================
        # SNIPER SELL (PUT)
        # ==========================
        if bajista:

            if (
                is_bullish(prev) and
                is_bearish(last) and
                last["close"] < prev["open"] and
                fuerza(last) > 0.5
            ):

                return {
                    "action": "put",
                    "score": 5,
                    "tipo": "sniper_sell"
                }

        return None

    except:
        return None
