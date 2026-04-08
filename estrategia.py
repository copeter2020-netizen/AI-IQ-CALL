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
# DETECTAR MERCADO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.tail(10)
    maximo = ultimas["max"].max()
    minimo = ultimas["min"].min()

    rango_total = maximo - minimo

    return rango_total < 0.0008  # ajustable

# =========================
# DETECTAR SOPORTE / RESISTENCIA
# =========================
def niveles(df):
    ultimas = df.tail(20)
    soporte = ultimas["min"].min()
    resistencia = ultimas["max"].max()
    return soporte, resistencia

# =========================
# DETECTAR ENTRADA
# =========================
def detectar_entrada(df):

    if len(df) < 30:
        return None

    df = df.copy()

    # EMA 20
    df["ema20"] = df["close"].ewm(span=20).mean()

    vela = df.iloc[-1]
    anterior = df.iloc[-2]

    soporte, resistencia = niveles(df)

    # =========================
    # FILTRO: NO OPERAR EN RANGO MEDIO
    # =========================
    if mercado_lateral(df):
        # SOLO operar en extremos del rango
        if vela["close"] < soporte + 0.0002:
            zona = "soporte"
        elif vela["close"] > resistencia - 0.0002:
            zona = "resistencia"
        else:
            return None
    else:
        zona = None

    # =========================
    # CONFIRMACIÓN DE VELA FUERTE
    # =========================
    vela_fuerte = body(vela) > (rango(vela) * 0.6)

    # =========================
    # SEÑALES
    # =========================

    # CALL
    if (
        vela["close"] > vela["ema20"] and
        es_alcista(vela) and
        vela_fuerte and
        (zona == "soporte" or not mercado_lateral(df))
    ):
        return "call"

    # PUT
    if (
        vela["close"] < vela["ema20"] and
        es_bajista(vela) and
        vela_fuerte and
        (zona == "resistencia" or not mercado_lateral(df))
    ):
        return "put"

    return None
