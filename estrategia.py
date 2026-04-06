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
# INDICADORES
# =========================
def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()

    subida = delta.clip(lower=0)
    bajada = -delta.clip(upper=0)

    media_subida = subida.rolling(periodo).mean()
    media_bajada = bajada.rolling(periodo).mean()

    rs = media_subida / media_bajada
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]


def calcular_ema(df, periodo=50):
    return df["close"].ewm(span=periodo, adjust=False).mean().iloc[-1]


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
# IMPULSO (CLAVE)
# =========================
def impulso_fuerte(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.75


def impulso_reciente_fuerte(df):
    ultimas = df.iloc[-5:]

    alcistas = 0
    bajistas = 0

    for _, v in ultimas.iterrows():
        if impulso_fuerte(v) and es_alcista(v):
            alcistas += 1
        if impulso_fuerte(v) and es_bajista(v):
            bajistas += 1

    if alcistas >= 3:
        return "alcista"

    if bajistas >= 3:
        return "bajista"

    return "neutral"


# =========================
# VALIDACIONES DE VELAS
# =========================
def confirmacion_fuerte(v):
    if rango(v) == 0:
        return False

    return (
        body(v) > rango(v) * 0.55 and  # más flexible
        body(v) > 0
    )


def rechazo_fuerte(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.3 or
        mecha_inf > body(v) * 1.3
    )


def vela_excesiva(df):
    ultimas = df.iloc[-10:]
    cuerpos = [body(v) for _, v in ultimas.iterrows()]

    promedio = np.mean(cuerpos)
    actual = body(df.iloc[-2])

    return actual > promedio * 2  # más flexible


def zona_mala(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango_total = resistencia - soporte

    if rango_total == 0:
        return True

    distancia = min(abs(precio - soporte), abs(precio - resistencia))

    return distancia > rango_total * 0.7  # más permisivo


# =========================
# MAIN
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 50:
            continue

        df = pd.DataFrame(velas)

        # INDICADORES
        rsi = calcular_rsi(df)
        ema = calcular_ema(df)
        precio = df["close"].iloc[-1]

        if mercado_lateral(df):
            continue

        if tendencia_fuerte(df) != "neutral":
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        if vela_excesiva(df):
            continue

        # 🔥 FILTRO MÁS IMPORTANTE
        impulso = impulso_reciente_fuerte(df)

        bloquear_put = impulso == "alcista"
        bloquear_call = impulso == "bajista"

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]

        score = 0

        # =========================
        # PUT
        # =========================
        if not bloquear_put and v_manipulacion["max"] >= resistencia:

            if rsi > 60:
                score += 2
            else:
                continue

            if precio < ema:
                score += 2
            else:
                continue

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 1

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

            if rsi < 40:
                score += 2
            else:
                continue

            if precio > ema:
                score += 2
            else:
                continue

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 1

            if impulso_fuerte(v_confirmacion):
                score += 1

            if not confirmacion_fuerte(v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor_score = score
                mejor = (par, "call", score)

    return mejor
