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
# SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# CERCA DE ZONA
# ==========================
def cerca(valor, nivel, rango_total):
    return abs(valor - nivel) < rango_total * 0.05


# ==========================
# MERCADO ACTIVO
# ==========================
def mercado_activo(df):
    highs = df["max"].values
    lows = df["min"].values

    vol = np.mean(highs[-5:] - lows[-5:])
    rango_total = max(highs[-20:]) - min(lows[-20:])

    return rango_total > vol * 2


# ==========================
# 🔥 ENTRADA OCULTA
# ==========================
def detectar_entrada_oculta(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        if not mercado_activo(df):
            continue

        soporte, resistencia = niveles(df)
        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]  # vela ACTUAL (clave)
        prev = df.iloc[-2]

        score = 0

        # ======================
        # 🔥 SOPORTE → CALL
        # ======================
        if cerca(v["min"], soporte, rango_total):

            if mecha_inf(v) > body(v):
                score += 2

            if es_alcista(v) and body(v) > rango(v) * 0.4:
                score += 2

        # ======================
        # 🔥 RESISTENCIA → PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if mecha_sup(v) > body(v):
                score += 2

            if es_bajista(v) and body(v) > rango(v) * 0.4:
                score += 2

        if score > mejor_score:
            direccion = "call" if es_alcista(v) else "put"
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 3:
        return mejor

    return None
