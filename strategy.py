import pandas as pd


# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])


def candle_range(c):
    return c["max"] - c["min"]


def fuerza(c):
    r = candle_range(c)
    if r == 0:
        return 0
    return body(c) / r


def is_bullish(c):
    return c["close"] > c["open"]


def is_bearish(c):
    return c["close"] < c["open"]


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 5:
            return None

        # 🔥 SOLO LA VELA QUE ACABA DE CERRAR
        last = df.iloc[-1]

        f = fuerza(last)

        # ==========================
        # CALL (movimiento alcista)
        # ==========================
        if is_bullish(last) and f > 0.5:
            return {
                "action": "call",
                "score": 10
            }

        # ==========================
        # PUT (movimiento bajista)
        # ==========================
        if is_bearish(last) and f > 0.5:
            return {
                "action": "put",
                "score": 10
            }

        return None

    except:
        return None
