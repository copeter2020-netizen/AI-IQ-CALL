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

    return np.mean(rangos) < (max(rangos) * 0.4)  # 🔥 más preciso


# =========================
# IMPULSO REAL
# =========================
def impulso(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.6


def impulso_previo(df):
    ultimas = df.iloc[-5:]

    fuertes = 0

    for _, v in ultimas.iterrows():
        if impulso(v):
            fuertes += 1

    return fuertes >= 3


# =========================
# BREAKOUT REAL
# =========================
def breakout_alcista(df):
    resistencia = df["max"].rolling(15).max().iloc[-3]
    return df["close"].iloc[-2] > resistencia


def breakout_bajista(df):
    soporte = df["min"].rolling(15).min().iloc[-3]
    return df["close"].iloc[-2] < soporte


# =========================
# FILTRO ANTI FAKE
# =========================
def fake_breakout(v):
    # mecha grande = posible manipulación
    if rango(v) == 0:
        return True

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.5 or
        mecha_inf > body(v) * 1.5
    )


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

        # 🔥 nuevo filtro clave
        if not impulso_previo(df):
            continue

        v = df.iloc[-2]

        score = 0

        # =========================
        # CALL
        # =========================
        if breakout_alcista(df):

            if fake_breakout(v):
                continue  # 🚫 evita trampas

            if confirmacion_alcista(v):
                score += 3

            if impulso_previo(df):
                score += 2

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

        # =========================
        # PUT
        # =========================
        if breakout_bajista(df):

            if fake_breakout(v):
                continue

            if confirmacion_bajista(v):
                score += 3

            if impulso_previo(df):
                score += 2

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

    return mejor
