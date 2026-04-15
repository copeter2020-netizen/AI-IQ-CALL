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
# AGOTAMIENTO
# =========================
def agotamiento(v):
    if rango(v) == 0:
        return None

    cuerpo = body(v)
    rango_total = rango(v)

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    # agotamiento bajista → posible subida
    if (
        es_bajista(v) and
        cuerpo < rango_total * 0.4 and
        mecha_inf > cuerpo * 2
    ):
        return "call"

    # agotamiento alcista → posible bajada
    if (
        es_alcista(v) and
        cuerpo < rango_total * 0.4 and
        mecha_sup > cuerpo * 2
    ):
        return "put"

    return None
S

# =========================
# CAMBIO DE TENDENCIA
# =========================
def cambio_tendencia(v, tipo):

    if rango(v) == 0:
        return False

    cuerpo = body(v)
    rango_total = rango(v)

    # fuerza mínima real
    if cuerpo < rango_total * 0.6:
        return False

    if tipo == "call":
        return es_alcista(v)

    if tipo == "put":
        return es_bajista(v)

    return False


# =========================
# DETECCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 12:
            continue

        df = pd.DataFrame(velas)

        v_prev = df.iloc[-2]   # vela de agotamiento
        v_actual = df.iloc[-1] # vela de cambio

        tipo = agotamiento(v_prev)

        if not tipo:
            continue

        if not cambio_tendencia(v_actual, tipo):
            continue

        # score simple pero efectivo
        score = 12

        mejor = (par, tipo, score)
        break

    return mejor
