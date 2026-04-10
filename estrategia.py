import pandas as pd


# =========================
# UTILIDADES
# =========================
def es_alcista(v):
    return v["close"] > v["open"]


def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# TENDENCIA (estructura real)
# =========================
def tendencia(df):
    ultimas = df.iloc[-20:]

    maximos = ultimas["max"]
    minimos = ultimas["min"]

    if maximos.is_monotonic_increasing and minimos.is_monotonic_increasing:
        return "alcista"

    if maximos.is_monotonic_decreasing and minimos.is_monotonic_decreasing:
        return "bajista"

    return "neutral"


# =========================
# DETECTAR CORRECCIÓN
# =========================
def correccion_alcista(df):
    ultimas = df.iloc[-5:-1]

    rojas = sum(es_bajista(v) for _, v in ultimas.iterrows())

    return 2 <= rojas <= 4


def correccion_bajista(df):
    ultimas = df.iloc[-5:-1]

    verdes = sum(es_alcista(v) for _, v in ultimas.iterrows())

    return 2 <= verdes <= 4


# =========================
# CONFIRMACIÓN DE REENTRADA
# =========================
def confirmacion_alcista(v):
    return es_alcista(v)


def confirmacion_bajista(v):
    return es_bajista(v)


# =========================
# MAIN
# =========================
def detectar_entrada_oculta(data):

    par = "EURUSD-OTC"

    if par not in data:
        return None

    velas = data[par]

    if len(velas) < 180:
        return None

    df = pd.DataFrame(velas)

    dir_tendencia = tendencia(df)

    v_actual = df.iloc[-1]

    # =========================
    # COMPRA
    # =========================
    if dir_tendencia == "alcista":

        if correccion_alcista(df):

            if confirmacion_alcista(v_actual):
                return (par, "call", 10)

    # =========================
    # VENTA
    # =========================
    if dir_tendencia == "bajista":

        if correccion_bajista(df):

            if confirmacion_bajista(v_actual):
                return (par, "put", 10)

    return None
