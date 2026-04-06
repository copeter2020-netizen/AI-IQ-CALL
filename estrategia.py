import numpy as np
import pandas as pd

# =========================
# UTILIDADES
# =========================
def body(v):
    return abs(v["close"] - v["open"])

def rango(v):
    return v["max"] - v["min"]

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# TENDENCIA REAL
# =========================
def tendencia_real(df):
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "alcista"

    if ma20.iloc[-1] < ma50.iloc[-1]:
        return "bajista"

    return "neutral"


# =========================
# FILTRO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


# =========================
# IMPULSO FUERTE
# =========================
def impulso_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.7


# =========================
# DETECTAR SOBRE-EXTENSIÓN 🔥
# =========================
def sobre_extension(df):
    ultimas = df.iloc[-5:]

    fuertes = sum(
        body(v) > rango(v) * 0.6
        for _, v in ultimas.iterrows()
    )

    return fuertes >= 3


# =========================
# DETECTAR TECHO / SUELO 🔥
# =========================
def cerca_resistencia(df):
    maximo = df["max"].rolling(20).max().iloc[-2]
    precio = df["close"].iloc[-2]

    return abs(precio - maximo) < (maximo * 0.001)


def cerca_soporte(df):
    minimo = df["min"].rolling(20).min().iloc[-2]
    precio = df["close"].iloc[-2]

    return abs(precio - minimo) < (minimo * 0.001)


# =========================
# PULLBACK REAL 🔥
# =========================
def pullback_real_alcista(df):
    ultimas = df.iloc[-5:]

    impulso = sum(es_alcista(v) for _, v in ultimas.iloc[:3].iterrows()) >= 2
    retroceso = sum(es_bajista(v) for _, v in ultimas.iloc[3:5].iterrows()) >= 2

    return impulso and retroceso


def pullback_real_bajista(df):
    ultimas = df.iloc[-5:]

    impulso = sum(es_bajista(v) for _, v in ultimas.iloc[:3].iterrows()) >= 2
    retroceso = sum(es_alcista(v) for _, v in ultimas.iloc[3:5].iterrows()) >= 2

    return impulso and retroceso


# =========================
# RUPTURA DEL PULLBACK 🔥
# =========================
def ruptura_alcista(df):
    v = df.iloc[-2]
    prev = df.iloc[-3]

    return v["close"] > prev["max"]


def ruptura_bajista(df):
    v = df.iloc[-2]
    prev = df.iloc[-3]

    return v["close"] < prev["min"]


# =========================
# DETECTOR PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None

    for par, velas in data.items():

        if len(velas) < 50:
            continue

        df = pd.DataFrame(velas)

        # =========================
        # FILTROS BASE
        # =========================
        if mercado_lateral(df):
            continue

        if sobre_extension(df):
            continue

        tendencia = tendencia_real(df)

        v_confirmacion = df.iloc[-2]

        # =========================
        # 🟢 CALL
        # =========================
        if tendencia == "alcista":

            if cerca_resistencia(df):
                continue

            if not pullback_real_alcista(df):
                continue

            if not ruptura_alcista(df):
                continue

            if not impulso_fuerte(v_confirmacion):
                continue

            return (par, "call", 1)

        # =========================
        # 🔴 PUT
        # =========================
        if tendencia == "bajista":

            if cerca_soporte(df):
                continue

            if not pullback_real_bajista(df):
                continue

            if not ruptura_bajista(df):
                continue

            if not impulso_fuerte(v_confirmacion):
                continue

            return (par, "put", 1)

    return mejor
