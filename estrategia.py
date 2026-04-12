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
# VOLATILIDAD
# =========================
def volatilidad(df):
    rangos = df["max"] - df["min"]
    return rangos.rolling(14).mean().iloc[-1]


# =========================
# NIVELES DINÁMICOS
# =========================
def niveles(df):

    vol = volatilidad(df)

    ultimos_rangos = (df["max"] - df["min"]).tail(10)
    rango_medio = ultimos_rangos.mean()

    if rango_medio > vol * 1.2:
        ventana = 10
    elif rango_medio < vol * 0.8:
        ventana = 30
    else:
        ventana = 20

    soporte = df["min"].rolling(ventana).min().iloc[-2]
    resistencia = df["max"].rolling(ventana).max().iloc[-2]

    return soporte, resistencia


# =========================
# MERCADO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


# =========================
# 🔥 NUEVA TENDENCIA (3 HORAS + MOMENTUM)
# =========================
def tendencia_fuerte(df):

    if len(df) < 180:
        return "neutral"

    # 📊 ESTRUCTURA 3 HORAS
    estructura = df.tail(180)

    max_actual = estructura["max"].iloc[-1]
    min_actual = estructura["min"].iloc[-1]

    max_pasado = estructura["max"].iloc[0]
    min_pasado = estructura["min"].iloc[0]

    # 📈 DIRECCIÓN GENERAL
    estructura_alcista = max_actual > max_pasado and min_actual > min_pasado
    estructura_bajista = max_actual < max_pasado and min_actual < min_pasado

    # ⚡ MOMENTUM ACTUAL (últimas 5 velas)
    ultimas = df.tail(5)

    verdes = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    rojas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())

    momentum_alcista = verdes >= 3
    momentum_bajista = rojas >= 3

    # 🎯 DECISIÓN FINAL
    if estructura_alcista and momentum_alcista:
        return "alcista"

    if estructura_bajista and momentum_bajista:
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

    return body(v) > rango(v) * 0.7


def rechazo_fuerte(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.2 or
        mecha_inf > body(v) * 1.2
    )


def zona_mala(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango_total = resistencia - soporte

    if rango_total == 0:
        return True

    distancia = min(abs(precio - soporte), abs(precio - resistencia))

    return distancia > rango_total * 0.75


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
        if not bloquear_put and v_manipulacion["max"] >= resistencia:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 1

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 8 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

        # =========================
        # CALL
        # =========================
        if not bloquear_call and v_manipulacion["min"] <= soporte:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 1

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

    return mejor
