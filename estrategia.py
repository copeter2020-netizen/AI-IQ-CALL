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


def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-2]
    resistencia = df["max"].rolling(20).max().iloc[-2]
    return soporte, resistencia


def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


def micro_tendencia(df):
    ultimas = df.iloc[-5:]

    verdes = sum(es_alcista(v) for _, v in ultimas.iterrows())
    rojas = sum(es_bajista(v) for _, v in ultimas.iterrows())

    if verdes >= 4:
        return "alcista"

    if rojas >= 4:
        return "bajista"

    return "neutral"


def tendencia_fuerte(df):
    ultimas = df.iloc[-6:]

    verdes = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    rojas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())

    if verdes >= 5:
        return "alcista"

    if rojas >= 5:
        return "bajista"

    return "neutral"


def confirmacion_fuerte(v):
    return body(v) > rango(v) * 0.6


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

    return distancia > rango_total * 0.6


# 🔥 NUEVO: evitar retrocesos
def es_retroceso(df):
    ultimas = df.iloc[-5:]
    altos = [v["max"] for _, v in ultimas.iterrows()]
    bajos = [v["min"] for _, v in ultimas.iterrows()]

    return altos[-1] > altos[0] and bajos[-1] > bajos[0]


# 🔥 NUEVO: evitar señal débil
def confirmacion_debil(df):
    ultimas = df.iloc[-2:]
    return ultimas.iloc[-1]["close"] < ultimas.iloc[-1]["open"] and \
           ultimas.iloc[-2]["close"] > ultimas.iloc[-2]["open"]


def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 30:
            continue

        df = pd.DataFrame(velas)

        if mercado_lateral(df):
            continue

        if tendencia_fuerte(df) != "neutral":
            continue

        if es_retroceso(df):  # 🔥 NUEVO
            continue

        if confirmacion_debil(df):  # 🔥 NUEVO
            continue

        tendencia = micro_tendencia(df)
        if tendencia != "neutral":
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        v_manipulacion = df.iloc[-3]
        v_confirmacion = df.iloc[-2]
        v_siguiente = df.iloc[-1]  # 🔥 NUEVO

        score = 0

        # =========================
        # PUT
        # =========================
        if v_manipulacion["max"] >= resistencia:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 3

            if not confirmacion_fuerte(v_confirmacion):
                continue

            # 🔥 DOBLE CONFIRMACIÓN REAL
            if v_siguiente["close"] >= v_confirmacion["close"]:
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

        # =========================
        # CALL
        # =========================
        if v_manipulacion["min"] <= soporte:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 3

            if not confirmacion_fuerte(v_confirmacion):
                continue

            # 🔥 DOBLE CONFIRMACIÓN REAL
            if v_siguiente["close"] <= v_confirmacion["close"]:
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

    return mejor
