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
    soporte = df["min"].rolling(20).min().iloc[-2]
    resistencia = df["max"].rolling(20).max().iloc[-2]
    return soporte, resistencia


def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


def tendencia_fuerte(df):
    ultimas = df.iloc[-6:]

    verdes = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    rojas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())

    if verdes >= 5:
        return "alcista"

    if rojas >= 5:
        return "bajista"

    return "neutral"


# =========================
# IMPULSO
# =========================
def impulso_fuerte(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.7


# =========================
# VELA DOMINANTE
# =========================
def direccion_ultima_fuerte(df):
    ultimas = df.iloc[-10:]
    cuerpos = [body(v) for _, v in ultimas.iterrows()]
    promedio = np.mean(cuerpos)

    v = df.iloc[-2]

    if body(v) > promedio * 1.8:
        if es_alcista(v):
            return "alcista"
        elif es_bajista(v):
            return "bajista"

    return "neutral"


# =========================
# CONTINUACIÓN
# =========================
def continuacion_alcista(df):
    ultimas = df.iloc[-4:]
    return sum(es_alcista(v) for _, v in ultimas.iterrows()) >= 3


def continuacion_bajista(df):
    ultimas = df.iloc[-4:]
    return sum(es_bajista(v) for _, v in ultimas.iterrows()) >= 3


# =========================
# MICRO ESTRUCTURA (NUEVO)
# =========================
def mini_giro_alcista(df):
    ultimas = df.iloc[-3:]
    return all(es_alcista(v) for _, v in ultimas.iterrows())


def mini_giro_bajista(df):
    ultimas = df.iloc[-3:]
    return all(es_bajista(v) for _, v in ultimas.iterrows())


# =========================
# VALIDACIONES
# =========================
def confirmacion_fuerte(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.55


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
    return distancia > rango_total * 0.6


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

        # FILTROS BASE
        if mercado_lateral(df):
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        tendencia = tendencia_fuerte(df)
        direccion_fuerte = direccion_ultima_fuerte(df)

        # BLOQUEOS INTELIGENTES
        bloquear_put = False
        bloquear_call = False

        # 🚫 CONTINUACIÓN
        if continuacion_alcista(df):
            bloquear_put = True

        if continuacion_bajista(df):
            bloquear_call = True

        # 🚫 VELA DOMINANTE
        if direccion_fuerte == "alcista":
            bloquear_put = True

        if direccion_fuerte == "bajista":
            bloquear_call = True

        # 🚫 TENDENCIA
        if tendencia == "alcista":
            bloquear_put = True

        if tendencia == "bajista":
            bloquear_call = True

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]

        score = 0

        # =========================
        # PUT
        # =========================
        if not bloquear_put and v_manipulacion["max"] >= resistencia:

            if not rechazo_fuerte(v_manipulacion):
                continue

            if not mini_giro_bajista(df):
                continue

            score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 1

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "put", score)

        # =========================
        # CALL
        # =========================
        if not bloquear_call and v_manipulacion["min"] <= soporte:

            if not rechazo_fuerte(v_manipulacion):
                continue

            if not mini_giro_alcista(df):
                continue

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
