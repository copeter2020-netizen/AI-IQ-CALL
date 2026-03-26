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


def upper_wick(c):
    return c["max"] - max(c["close"], c["open"])


def lower_wick(c):
    return min(c["close"], c["open"]) - c["min"]


def is_bullish(c):
    return c["close"] > c["open"]


def is_bearish(c):
    return c["close"] < c["open"]


# ==========================
# FILTROS
# ==========================
def es_doji(c):
    return fuerza(c) < 0.2


def es_indecision(c):
    return fuerza(c) < 0.35


def es_ahorcamiento(c):
    return upper_wick(c) > body(c) * 1.5 or lower_wick(c) > body(c) * 1.5


def es_vela_fuerte(c):
    return (
        fuerza(c) > 0.5 and
        not es_doji(c) and
        not es_indecision(c) and
        not es_ahorcamiento(c)
    )


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 5:
            return None

        last = df.iloc[-1]

        # 🔥 SOLO VELAS LIMPIAS DE CONTINUACIÓN
        if not es_vela_fuerte(last):
            return None

        # ==========================
        # CALL
        # ==========================
        if is_bullish(last):
            return {
                "action": "call",
                "score": 10
            }

        # ==========================
        # PUT
        # ==========================
        if is_bearish(last):
            return {
                "action": "put",
                "score": 10
            }

        return None

    except:
        return None
