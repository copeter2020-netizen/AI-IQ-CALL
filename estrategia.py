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


def tendencia_real(df):
    ultimas = df.iloc[-10:]

    maximos = [v["max"] for _, v in ultimas.iterrows()]
    minimos = [v["min"] for _, v in ultimas.iterrows()]

    if maximos[-1] < maximos[0] and minimos[-1] < minimos[0]:
        return "bajista"

    if maximos[-1] > maximos[0] and minimos[-1] > minimos[0]:
        return "alcista"

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


# 🔥 NUEVO — DOBLE CONFIRMACIÓN
def doble_confirmacion(df, direccion):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    if direccion == "call":
        return es_alcista(v1) and es_alcista(v2)

    if direccion == "put":
        return es_bajista(v1) and es_bajista(v2)

    return False


# 🔥 NUEVO — FUERZA REAL
def fuerza_movimiento(df, direccion):
    v = df.iloc[-2]

    if direccion == "call":
        return body(v) > rango(v) * 0.6 and es_alcista(v)

    if direccion == "put":
        return body(v) > rango(v) * 0.6 and es_bajista(v)

    return False


# 🔥 NUEVO — ANTI PULLBACK
def pullback_debil(df):
    ultimas = df.iloc[-4:]

    cambios = [v["close"] - v["open"] for _, v in ultimas.iterrows()]

    verdes = sum(c > 0 for c in cambios)
    rojas = sum(c < 0 for c in cambios)

    return verdes == 1 or rojas == 1


# 🔥 NUEVO — ACUMULACIÓN (ENTRADA TEMPRANA)
def zona_acumulacion(df):
    ultimas = df.iloc[-5:]

    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if max(rangos) == 0:
        return False

    return np.mean(rangos) < (max(rangos) * 0.5)


# 🔥 NUEVO — FRENADO
def frenado(df):
    ultimas = df.iloc[-4:]

    cambios = [abs(v["close"] - v["open"]) for _, v in ultimas.iterrows()]

    return cambios[-1] < cambios[0]


def zona_mala(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango_total = resistencia - soporte

    if rango_total == 0:
        return True

    distancia = min(abs(precio - soporte), abs(precio - resistencia))

    return distancia > rango_total * 0.6


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

        if tendencia_real(df) != "neutral":
            continue

        if micro_tendencia(df) != "neutral":
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        if pullback_debil(df):
            continue

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]

        # =========================
        # 🔥 ENTRADA TEMPRANA (SNIPER)
        # =========================
        if zona_acumulacion(df) and frenado(df):

            if v_manipulacion["min"] <= soporte:
                return (par, "call", 10)

            if v_manipulacion["max"] >= resistencia:
                return (par, "put", 10)

        score = 0

        # =====================
        # PUT
        # =====================
        if v_manipulacion["max"] >= resistencia:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 3

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if not doble_confirmacion(df, "put"):
                continue

            if not fuerza_movimiento(df, "put"):
                continue

            if score >= 5:
                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "put", score)

        # =====================
        # CALL
        # =====================
        if v_manipulacion["min"] <= soporte:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 3

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if not doble_confirmacion(df, "call"):
                continue

            if not fuerza_movimiento(df, "call"):
                continue

            if score >= 5:
                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "call", score)

    return mejor
