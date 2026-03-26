import pandas as pd


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
# NUEVA LÓGICA INSTITUCIONAL
# ==========================
def patron_continuidad(df):

    if len(df) < 5:
        return None

    c1 = df.iloc[-1]  # confirmación
    c2 = df.iloc[-2]  # retroceso
    c3 = df.iloc[-3]  # impulso
    c4 = df.iloc[-4]

    # ======================
    # COMPRA
    # ======================
    if (
        is_bullish(c3) and
        c3["close"] > c4["close"] and  # rompimiento
        is_bearish(c2) and             # retroceso
        is_bullish(c1) and             # confirmación
        fuerza(c1) > 0.5
    ):
        return "call"

    # ======================
    # VENTA
    # ======================
    if (
        is_bearish(c3) and
        c3["close"] < c4["close"] and
        is_bullish(c2) and
        is_bearish(c1) and
        fuerza(c1) > 0.5
    ):
        return "put"

    return None


# ==========================
# TU ESTRATEGIA ORIGINAL + FILTRO NUEVO
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 30:
            return None

        # 🔥 TU ESTRATEGIA ORIGINAL (NO MODIFICADA)
        last = df.iloc[-1]
        prev = df.iloc[-2]

        if last["close"] < prev["close"]:
            return None

        if fuerza(last) < 0.5:
            return None

        # ==========================
        # NUEVO FILTRO (OBLIGATORIO)
        # ==========================
        patron = patron_continuidad(df)

        if not patron:
            return None

        return {
            "action": patron,
            "score": 10
        }

    except:
        return None
