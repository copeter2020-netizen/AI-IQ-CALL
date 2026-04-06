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
# TENDENCIA REAL (BASE)
# =========================
def tendencia_real(df):
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "alcista"

    if ma20.iloc[-1] < ma50.iloc[-1]:
        return "bajista"

    return "neutral"


# =========================
# FILTRO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


# =========================
# IMPULSO FUERTE
# =========================
def impulso_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.6


# =========================
# PULLBACK DETECTOR 🔥
# =========================
def es_pullback_alcista(df):
    ultimas = df.iloc[-4:]

    # tendencia previa alcista
    impulso = es_alcista(ultimas.iloc[0]) and es_alcista(ultimas.iloc[1])

    # retroceso
    retroceso = es_bajista(ultimas.iloc[2])

    return impulso and retroceso


def es_pullback_bajista(df):
    ultimas = df.iloc[-4:]

    impulso = es_bajista(ultimas.iloc[0]) and es_bajista(ultimas.iloc[1])
    retroceso = es_alcista(ultimas.iloc[2])

    return impulso and retroceso


# =========================
# CONFIRMACIÓN DE ENTRADA 🔥
# =========================
def confirmacion_alcista(v):
    return es_alcista(v) and impulso_fuerte(v)


def confirmacion_bajista(v):
    return es_bajista(v) and impulso_fuerte(v)


# =========================
# ENTRADA TARDE (CLAVE)
# =========================
def entrada_tarde(df):
    ultimas = df.iloc[-3:]

    cuerpos = [body(v) for _, v in ultimas.iterrows()]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    velas_fuertes = sum(c > r * 0.6 for c, r in zip(cuerpos, rangos))

    return velas_fuertes >= 2


# =========================
# DETECTOR PRINCIPAL (NUEVO)
# =========================
def detectar_entrada_oculta(data):

    mejor = None

    for par, velas in data.items():

        if len(velas) < 50:
            continue

        df = pd.DataFrame(velas)

        # =========================
        # FILTROS BASE
        # =========================
        if mercado_lateral(df):
            continue

        if entrada_tarde(df):
            continue

        tendencia = tendencia_real(df)

        v_confirmacion = df.iloc[-2]  # vela donde entras
        v_pullback = df.iloc[-3]      # retroceso

        # =========================
        # 🟢 SETUP CALL (CONTINUACIÓN ALCISTA)
        # =========================
        if tendencia == "alcista":

            if not es_pullback_alcista(df):
                continue

            if not confirmacion_alcista(v_confirmacion):
                continue

            # entrada EXACTA binarias
            return (par, "call", 1)

        # =========================
        # 🔴 SETUP PUT (CONTINUACIÓN BAJISTA)
        # =========================
        if tendencia == "bajista":

            if not es_pullback_bajista(df):
                continue

            if not confirmacion_bajista(v_confirmacion):
                continue

            return (par, "put", 1)

    return mejor
