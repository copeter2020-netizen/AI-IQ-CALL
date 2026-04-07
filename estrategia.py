import numpy as np
import pandas as pd


def body(v):
    return abs(v["close"] - v["open"])


def rango(v):
    return v["max"] - v["min"]


def es_alcista(v):
    return v["close"] > v["open"]


def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# ESTRUCTURA
# =========================
def niveles(df):
    soporte = df["min"].rolling(15).min().iloc[-2]
    resistencia = df["max"].rolling(15).max().iloc[-2]
    return soporte, resistencia


def mercado_lateral(df):
    ultimas = df.iloc[-5:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if not rangos:
        return True

    return np.mean(rangos) < (max(rangos) * 0.4)


def tendencia_fuerte(df):
    ultimas = df.iloc[-5:]

    verdes = sum(es_alcista(v) for _, v in ultimas.iterrows())
    rojas = sum(es_bajista(v) for _, v in ultimas.iterrows())

    if verdes >= 4:
        return "alcista"

    if rojas >= 4:
        return "bajista"

    return "neutral"


# =========================
# VALIDACIONES
# =========================
def confirmacion_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.5


def impulso_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.65


def rechazo_fuerte(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.3 or
        mecha_inf > body(v) * 1.3
    )


def zona_mala(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango_total = resistencia - soporte

    if rango_total == 0:
        return True

    distancia = min(abs(precio - soporte), abs(precio - resistencia))

    return distancia > rango_total * 0.8


# =========================
# MAIN
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        df = pd.DataFrame(velas)

        if mercado_lateral(df):
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        tendencia = tendencia_fuerte(df)

        bloquear_put = tendencia == "alcista"
        bloquear_call = tendencia == "bajista"

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]

        score = 0

        # =========================
        # PUT
        # =========================
        if not bloquear_put and v_manipulacion["max"] >= resistencia * 0.998:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 2

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

        # =========================
        # CALL
        # =========================
        if not bloquear_call and v_manipulacion["min"] <= soporte * 1.002:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 2

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

    return mejor
