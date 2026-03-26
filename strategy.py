import pandas as pd


# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])


def candle_range(c):
    return c["max"] - c["min"]


# ==========================
# RANGO (CANAL HORIZONTAL)
# ==========================
def resistencia(df):
    return df["max"].rolling(20).max().iloc[-1]


def soporte(df):
    return df["min"].rolling(20).min().iloc[-1]


def es_rango(df):
    alto = resistencia(df)
    bajo = soporte(df)

    rango = alto - bajo

    # rango pequeño = lateral
    return rango < (df["close"].iloc[-1] * 0.004)


# ==========================
# RECHAZOS
# ==========================
def rechazo_superior(c):
    upper = c["max"] - max(c["close"], c["open"])
    return upper > body(c)


def rechazo_inferior(c):
    lower = min(c["close"], c["open"]) - c["min"]
    return lower > body(c)


# ==========================
# CERCA DE NIVELES
# ==========================
def cerca_resistencia(c, res):
    return abs(c["max"] - res) < (res * 0.0015)


def cerca_soporte(c, sup):
    return abs(c["min"] - sup) < (sup * 0.0015)


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 25:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        res = resistencia(df)
        sup = soporte(df)

        # ==========================
        # VALIDAR RANGO
        # ==========================
        if not es_rango(df):
            return None

        # ==========================
        # 🔼 PUT (RESISTENCIA)
        # ==========================
        if (
            cerca_resistencia(prev, res)
            and rechazo_superior(prev)
            and prev["close"] < prev["open"]  # vela roja
        ):
            return {
                "action": "put",
                "score": 10
            }

        # ==========================
        # 🔽 CALL (SOPORTE)
        # ==========================
        if (
            cerca_soporte(prev, sup)
            and rechazo_inferior(prev)
            and prev["close"] > prev["open"]  # vela verde
        ):
            return {
                "action": "call",
                "score": 10
            }

        return None

    except:
        return None
