import pandas as pd
import numpy as np


def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

def body(v):
    return abs(v["close"] - v["open"])

def rango(v):
    return v["max"] - v["min"]


# =========================
# 🔥 TENDENCIA REAL
# =========================
def tendencia(df):
    ultimas = df.iloc[-6:]

    alcistas = sum(es_alcista(v) for _, v in ultimas.iterrows())
    bajistas = sum(es_bajista(v) for _, v in ultimas.iterrows())

    if alcistas >= 4:
        return "alcista"

    if bajistas >= 4:
        return "bajista"

    return "lateral"


# =========================
# 🔥 IMPULSO REAL
# =========================
def impulso(df):
    ultimas = df.iloc[-3:]

    fuertes = 0

    for _, v in ultimas.iterrows():
        if rango(v) == 0:
            continue

        if body(v) > rango(v) * 0.6:
            fuertes += 1

    return fuertes >= 2


# =========================
# 🔥 FILTRO DE ENTRADA
# =========================
def buena_entrada(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.5


# =========================
# 🚀 MAIN
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 30:
            continue

        df = pd.DataFrame(velas)

        dir_tendencia = tendencia(df)

        if dir_tendencia == "lateral":
            continue

        if not impulso(df):
            continue

        v = df.iloc[-2]

        score = 0

        # =========================
        # CALL (continuidad alcista)
        # =========================
        if dir_tendencia == "alcista":

            if es_alcista(v):
                score += 2

            if buena_entrada(v):
                score += 2

            if score >= 3 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

        # =========================
        # PUT (continuidad bajista)
        # =========================
        if dir_tendencia == "bajista":

            if es_bajista(v):
                score += 2

            if buena_entrada(v):
                score += 2

            if score >= 3 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

    return mejor        if breakout_bajista(df):

            if confirmacion_bajista(v):
                score += 6

            if score >= 6 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

    return mejor
