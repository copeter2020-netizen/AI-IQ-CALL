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
# 🔥 CONSOLIDACIÓN PURA
# =========================
def es_consolidacion(df):
    ultimas = df.iloc[-10:]

    maximo = ultimas["max"].max()
    minimo = ultimas["min"].min()

    rango_total = maximo - minimo

    if rango_total == 0:
        return False

    rangos = [rango(v) for _, v in ultimas.iterrows()]

    return np.mean(rangos) < (rango_total * 0.4)


# =========================
# 🎯 MAIN (SIN FILTROS)
# =========================
def detectar_entrada_oculta(data):

    mejor = None

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        df = pd.DataFrame(velas)

        # SOLO CONSOLIDACIÓN
        if not es_consolidacion(df):
            continue

        v = df.iloc[-2]

        # 🔴 SI VELA BAJISTA → PUT
        if es_bajista(v):
            mejor = (par, "put", 1)

        # 🟢 SI VELA ALCISTA → CALL
        elif es_alcista(v):
            mejor = (par, "call", 1)

    return mejor
