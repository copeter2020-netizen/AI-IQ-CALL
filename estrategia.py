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
# MERCADO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.tail(10)
    maximo = ultimas["max"].max()
    minimo = ultimas["min"].min()

    return (maximo - minimo) < 0.0008

# =========================
# SOPORTE / RESISTENCIA
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

    if df is None or len(df) < 30:
        return None

    df = df.copy()

    # EMA 20
    df["ema20"] = df["close"].ewm(span=20).mean()

    vela = df.iloc[-1]

    soporte, resistencia = niveles(df)

    lateral = mercado_lateral(df)

    # =========================
    # VELA FUERTE
    # =========================
    vela_fuerte = body(vela) > (rango(vela) * 0.6)

    # =========================
    # CONDICIONES CALL
    # =========================
    if (
        vela["close"] > vela["ema20"] and
        es_alcista(vela) and
        vela_fuerte and
        (
            not lateral or
            vela["close"] <= soporte + 0.0002
        )
    ):
        return "call"

    # =========================
    # CONDICIONES PUT
    # =========================
    if (
        vela["close"] < vela["ema20"] and
        es_bajista(vela) and
        vela_fuerte and
        (
            not lateral or
            vela["close"] >= resistencia - 0.0002
        )
    ):
        return "put"

    return None
