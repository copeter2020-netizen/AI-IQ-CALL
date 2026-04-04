import pandas as pd
import numpy as np

# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def mecha_sup(c):
    return c["max"] - max(c["open"], c["close"])

def mecha_inf(c):
    return min(c["open"], c["close"]) - c["min"]

def es_alcista(c):
    return c["close"] > c["open"]

def es_bajista(c):
    return c["close"] < c["open"]


# ==========================
# 🔥 SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# 🔥 DISTANCIA A ZONA (CLAVE)
# ==========================
def cerca_de_soporte(c, soporte, rango_total):
    return abs(c["min"] - soporte) < rango_total * 0.05

def cerca_de_resistencia(c, resistencia, rango_total):
    return abs(c["max"] - resistencia) < rango_total * 0.05


# ==========================
# 🔥 RECHAZO (LIQUIDEZ)
# ==========================
def rechazo_soporte(c):
    return mecha_inf(c) > body(c) * 1.5

def rechazo_resistencia(c):
    return mecha_sup(c) > body(c) * 1.5


# ==========================
# 🔥 CONTINUIDAD (CONFIRMACIÓN)
# ==========================
def continuidad_alcista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r

    return (
        es_alcista(c) and
        pos > 0.7 and
        body(c) > r * 0.5 and
        mecha_sup(c) < body(c) * 0.4
    )


def continuidad_bajista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r

    return (
        es_bajista(c) and
        pos < 0.3 and
        body(c) > r * 0.5 and
        mecha_inf(c) < body(c) * 0.4
    )


# ==========================
# 🔥 MERCADO ACTIVO (ANTI LATERAL)
# ==========================
def mercado_activo(df):
    highs = df["max"].values
    lows = df["min"].values

    vol_actual = np.mean(highs[-5:] - lows[-5:])
    vol_pasada = np.mean(highs[-30:] - lows[-30:])

    rango_total = max(highs[-20:]) - min(lows[-20:])

    if vol_actual < vol_pasada * 0.8:
        return False

    if rango_total < vol_actual * 2:
        return False

    return True


# ==========================
# 🔥 FUNCIÓN PRINCIPAL
# ==========================
def detectar_mejor_entrada(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        # 🔥 FILTRO MERCADO
        if not mercado_activo(df):
            continue

        soporte, resistencia = niveles(df)

        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        c1 = df.iloc[-1]  # confirmación
        c2 = df.iloc[-2]  # rechazo

        score = 0

        # ======================
        # 🔥 CALL (SOPORTE)
        # ======================
        if cerca_de_soporte(c2, soporte, rango_total):

            if rechazo_soporte(c2):
                score += 2

                if continuidad_alcista(c1):
                    score += 2

        # ======================
        # 🔥 PUT (RESISTENCIA)
        # ======================
        if cerca_de_resistencia(c2, resistencia, rango_total):

            if rechazo_resistencia(c2):
                score += 2

                if continuidad_bajista(c1):
                    score += 2

        # ======================
        # 🔥 SELECCIÓN
        # ======================
        if score > mejor_score:
            direccion = "call" if es_alcista(c1) else "put"
            mejor_score = score
            mejor = (par, direccion, score)

    # 🔥 SOLO ENTRADAS REALES
    if mejor and mejor_score >= 4:
        return mejor

    return None
