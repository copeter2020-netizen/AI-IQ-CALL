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
# DETECTAR CONSOLIDACIÓN
# =========================
def es_consolidacion(df):
    ultimas = df.iloc[-10:]

    maximo = ultimas["max"].max()
    minimo = ultimas["min"].min()

    rango_total = maximo - minimo

    # evitar rango muerto
    if rango_total == 0:
        return False

    # medir estabilidad del rango
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    return np.mean(rangos) < (rango_total * 0.4)


# =========================
# SOPORTE Y RESISTENCIA
# =========================
def niveles(df):
    ultimas = df.iloc[-10:]

    soporte = ultimas["min"].min()
    resistencia = ultimas["max"].max()

    return soporte, resistencia


# =========================
# FILTRO VELA FUERTE ❌
# =========================
def vela_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.7


# =========================
# ZONA DE ENTRADA
# =========================
def cerca_resistencia(precio, resistencia, rango_total):
    return abs(precio - resistencia) < (rango_total * 0.2)


def cerca_soporte(precio, soporte, rango_total):
    return abs(precio - soporte) < (rango_total * 0.2)


# =========================
# RECHAZO (CLAVE 🔥)
# =========================
def rechazo(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.2 or
        mecha_inf > body(v) * 1.2
    )


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

        # 🔥 SOLO CONSOLIDACIÓN
        if not es_consolidacion(df):
            continue

        soporte, resistencia = niveles(df)

        rango_total = resistencia - soporte
        if rango_total == 0:
            continue

        precio = df["close"].iloc[-1]

        v_confirmacion = df.iloc[-2]

        # ❌ evitar velas fuertes
        if vela_fuerte(v_confirmacion):
            continue

        score = 0

        # =========================
        # VENTA (arriba)
        # =========================
        if cerca_resistencia(precio, resistencia, rango_total):

            if es_bajista(v_confirmacion):
                score += 2

            if rechazo(v_confirmacion):
                score += 3

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

        # =========================
        # COMPRA (abajo)
        # =========================
        if cerca_soporte(precio, soporte, rango_total):

            if es_alcista(v_confirmacion):
                score += 2

            if rechazo(v_confirmacion):
                score += 3

            if score >= 4 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

    return mejor
