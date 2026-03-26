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
# FILTROS DE VELA
# ==========================
def es_doji(c):
    return fuerza(c) < 0.2


def es_indecision(c):
    return fuerza(c) < 0.35


def es_ahorcamiento(c):
    return upper_wick(c) > body(c) * 1.5 or lower_wick(c) > body(c) * 1.5


def es_vela_valida(c):
    return (
        fuerza(c) > 0.5 and
        not es_doji(c)
        and not es_indecision(c)
        and not es_ahorcamiento(c)
    )


# ==========================
# SOPORTE / RESISTENCIA
# ==========================
def resistencia(df):
    return df["max"].rolling(20).max().iloc[-1]


def soporte(df):
    return df["min"].rolling(20).min().iloc[-1]


# 🔥 BLOQUEO AJUSTADO (NO TAN AMPLIO)
def en_zona_prohibida(c, res, sup):

    margen = c["close"] * 0.0015  # 🔥 antes era muy grande

    cerca_res = abs(c["close"] - res) < margen
    cerca_sup = abs(c["close"] - sup) < margen

    return cerca_res or cerca_sup


# ==========================
# MICRO TENDENCIA
# ==========================
def micro_tendencia_alcista(df):
    ult = df.tail(4)
    return (
        ult.iloc[-1]["close"] > ult.iloc[-2]["close"] >
        ult.iloc[-3]["close"]
    )


def micro_tendencia_bajista(df):
    ult = df.tail(4)
    return (
        ult.iloc[-1]["close"] < ult.iloc[-2]["close"] <
        ult.iloc[-3]["close"]
    )


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 25:
            return None

        last = df.iloc[-1]

        # ==========================
        # FILTRO VELA
        # ==========================
        if not es_vela_valida(last):
            return None

        res = resistencia(df)
        sup = soporte(df)

        # ==========================
        # BLOQUEO S/R (CORREGIDO)
        # ==========================
        if en_zona_prohibida(last, res, sup):
            return None

        # ==========================
        # DIRECCIÓN + MICRO TENDENCIA
        # ==========================
        if is_bullish(last) and micro_tendencia_alcista(df):
            return {"action": "call", "score": 10}

        if is_bearish(last) and micro_tendencia_bajista(df):
            return {"action": "put", "score": 10}

        return None

    except:
        return None
