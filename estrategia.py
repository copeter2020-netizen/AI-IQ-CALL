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


# 🔥 NUEVO: estructura real del mercado
def estructura_bajista(df):
    highs = df["max"].iloc[-5:]
    lows = df["min"].iloc[-5:]

    return all(highs.iloc[i] < highs.iloc[i-1] for i in range(1, len(highs))) and \
           all(lows.iloc[i] < lows.iloc[i-1] for i in range(1, len(lows)))


def estructura_alcista(df):
    highs = df["max"].iloc[-5:]
    lows = df["min"].iloc[-5:]

    return all(highs.iloc[i] > highs.iloc[i-1] for i in range(1, len(highs))) and \
           all(lows.iloc[i] > lows.iloc[i-1] for i in range(1, len(lows)))


# 🔥 NUEVO: evita entrar después de impulso fuerte
def impulso_reciente(df):
    v = df.iloc[-2]
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.8


def confirmacion_fuerte(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.6


def ruptura_valida(v1, v2):
    # rompe la dirección previa
    return v2["close"] > v1["max"] or v2["close"] < v1["min"]


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


# 🔥 NUEVO: evita entrar tarde (vela ya movida)
def entrada_limpia(v):
    if rango(v) == 0:
        return False
    return abs(v["close"] - v["open"]) < (rango(v) * 0.2)


def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 30:
            continue

        df = pd.DataFrame(velas)

        if mercado_lateral(df):
            continue

        # ❌ BLOQUEA CONTRA TENDENCIA REAL
        if estructura_bajista(df) or estructura_alcista(df):
            continue

        # ❌ BLOQUEA IMPULSOS
        if impulso_reciente(df):
            continue

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]
        v_actual = df.iloc[-1]

        # ❌ EVITA ENTRADAS TARDÍAS
        if not entrada_limpia(v_actual):
            continue

        score = 0

        # =========================
        # PUT
        # =========================
        if v_manipulacion["max"] >= resistencia:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_bajista(v_confirmacion):
                score += 2

            if confirmacion_fuerte(v_confirmacion):
                score += 2

            if not ruptura_valida(v_manipulacion, v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor = (par, "put", score)
                mejor_score = score

        # =========================
        # CALL
        # =========================
        if v_manipulacion["min"] <= soporte:

            if rechazo_fuerte(v_manipulacion):
                score += 2

            if es_alcista(v_confirmacion):
                score += 2

            if confirmacion_fuerte(v_confirmacion):
                score += 2

            if not ruptura_valida(v_manipulacion, v_confirmacion):
                continue

            if score >= 5 and score > mejor_score:
                mejor = (par, "call", score)
                mejor_score = score

    return mejor
