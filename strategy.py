import pandas as pd
import numpy as np

# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def mecha_sup(c):
    return c["max"] - max(c["open"], c["close"])

def mecha_inf(c):
    return min(c["open"], c["close"]) - c["min"]

def es_alcista(c):
    return c["close"] > c["open"]

def es_bajista(c):
    return c["close"] < c["open"]


# ==========================
# 🔥 MERCADO ACTIVO (ANTI LATERAL)
# ==========================
def mercado_activo(df):
    highs = df["max"].values
    lows = df["min"].values

    vol_actual = np.mean(highs[-5:] - lows[-5:])
    vol_pasada = np.mean(highs[-30:] - lows[-30:])

    rango_total = max(highs[-20:]) - min(lows[-20:])

    if vol_actual < vol_pasada * 0.8:
        return False

    if rango_total < vol_actual * 2:
        return False

    return True


# ==========================
# 🔥 SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# 🔥 RECHAZO (LIQUIDEZ)
# ==========================
def rechazo_soporte(c):
    return mecha_inf(c) > body(c) * 1.5

def rechazo_resistencia(c):
    return mecha_sup(c) > body(c) * 1.5


# ==========================
# 🔥 CONTINUIDAD
# ==========================
def continuidad_alcista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r

    return (
        es_alcista(c) and
        pos > 0.75 and
        body(c) > r * 0.6 and
        mecha_sup(c) < body(c) * 0.3
    )


def continuidad_bajista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r

    return (
        es_bajista(c) and
        pos < 0.25 and
        body(c) > r * 0.6 and
        mecha_inf(c) < body(c) * 0.3
    )


# ==========================
# 🔥 SCORE DE CALIDAD
# ==========================
def score_setup(df, tipo):

    ultimas = df.tail(5)

    fuerza_total = sum(body(c) / rango(c) if rango(c) != 0 else 0 for _, c in ultimas.iterrows())

    return fuerza_total


# ==========================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================
def detectar_mejor_entrada(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        if not mercado_activo(df):
            continue

        soporte, resistencia = niveles(df)

        c1 = df.iloc[-1]
        c2 = df.iloc[-2]

        # ======================
        # CALL
        # ======================
        if c2["min"] <= soporte:

            if rechazo_soporte(c2) and continuidad_alcista(c1):

                score = score_setup(df, "call")

                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "call", score)

        # ======================
        # PUT
        # ======================
        if c2["max"] >= resistencia:

            if rechazo_resistencia(c2) and continuidad_bajista(c1):

                score = score_setup(df, "put")

                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "put", score)

    if mejor and mejor_score > 2.5:
        return mejor

    return None
