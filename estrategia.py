import pandas as pd
import numpy as np


# =========================
# RSI
# =========================
def calcular_rsi(df, period=14):
    delta = df["close"].diff()

    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)

    gain_avg = pd.Series(gain).rolling(period).mean()
    loss_avg = pd.Series(loss).rolling(period).mean()

    rs = gain_avg / (loss_avg + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    return rsi


# =========================
# VELAS
# =========================
def body(v):
    return abs(v["close"] - v["open"])


def rango(v):
    return v["max"] - v["min"]


def es_doji(v):
    if rango(v) == 0:
        return False
    return body(v) < rango(v) * 0.2


def es_pinbar(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 2 or
        mecha_inf > body(v) * 2
    )


def es_indecision(v):
    if rango(v) == 0:
        return False
    return body(v) < rango(v) * 0.3


def es_agotamiento(v):
    return es_doji(v) or es_pinbar(v) or es_indecision(v)


# =========================
# MAIN
# =========================
def detectar_entrada(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 50:
            continue

        df = pd.DataFrame(velas)

        df["rsi"] = calcular_rsi(df)

        rsi_actual = df["rsi"].iloc[-2]
        vela = df.iloc[-2]

        score = 0

        # =========================
        # CALL
        # =========================
        if rsi_actual < 30:

            score += 2

            if es_agotamiento(vela):
                score += 3

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call")

        # =========================
        # PUT
        # =========================
        if rsi_actual > 70:

            score += 2

            if es_agotamiento(vela):
                score += 3

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put")

    return mejor
