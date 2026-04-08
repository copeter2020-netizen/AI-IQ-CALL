import pandas as pd
import numpy as np


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
# FILTRO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


# =========================
# IMPULSO
# =========================
def impulso(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.6


# =========================
# BREAKOUT
# =========================
def breakout_alcista(df):
    resistencia = df["max"].rolling(15).max().iloc[-3]
    return df["close"].iloc[-2] > resistencia


def breakout_bajista(df):
    soporte = df["min"].rolling(15).min().iloc[-3]
    return df["close"].iloc[-2] < soporte


# =========================
# CONFIRMACIÓN
# =========================
def confirmacion_alcista(v):
    return es_alcista(v) and impulso(v)


def confirmacion_bajista(v):
    return es_bajista(v) and impulso(v)


# =========================
# MAIN
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 30:
            continue

        df = pd.DataFrame(velas)

        if mercado_lateral(df):
            continue

        v = df.iloc[-2]

        score = 0

        # =========================
        # CALL
        # =========================
        if breakout_alcista(df):

            if confirmacion_alcista(v):
                score += 6

            if score >= 6 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

        # =========================
        # PUT
        # =========================
        if breakout_bajista(df):

            if confirmacion_bajista(v):
                score += 6

            if score >= 6 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

    return mejor
