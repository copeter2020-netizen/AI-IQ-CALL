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
# SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    if len(df) < 20:
        return None, None

    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]

    return soporte, resistencia


# ==========================
# CERCA DE ZONA
# ==========================
def cerca(valor, nivel, rango_total):
    if nivel is None or rango_total == 0:
        return False
    return abs(valor - nivel) < rango_total * 0.05


# ==========================
# MERCADO ACTIVO
# ==========================
def mercado_activo(df):
    if len(df) < 20:
        return False

    highs = df["max"].values
    lows = df["min"].values

    vol = np.mean(highs[-5:] - lows[-5:])
    rango_total = max(highs[-20:]) - min(lows[-20:])

    if rango_total == 0:
        return False

    return rango_total > vol * 2


# ==========================
# 🔥 ENTRADA OCULTA
# ==========================
def detectar_entrada_oculta(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        try:
            df = pd.DataFrame(velas)

            # Validación de columnas
            if not all(col in df.columns for col in ["open", "close", "max", "min"]):
                continue

            if len(df) < 30:
                continue

            if not mercado_activo(df):
                continue

            soporte, resistencia = niveles(df)

            if soporte is None or resistencia is None:
                continue

            rango_total = max(df["max"].iloc[-20:]) - min(df["min"].iloc[-20:])

            if rango_total == 0:
                continue

            v = df.iloc[-1]

            score = 0

            # ======================
            # SOPORTE → CALL
            # ======================
            if cerca(v["min"], soporte, rango_total):

                if mecha_inf(v) > body(v):
                    score += 2

                if es_alcista(v) and body(v) > rango(v) * 0.4:
                    score += 2

            # ======================
            # RESISTENCIA → PUT
            # ======================
            if cerca(v["max"], resistencia, rango_total):

                if mecha_sup(v) > body(v):
                    score += 2

                if es_bajista(v) and body(v) > rango(v) * 0.4:
                    score += 2

            if score > mejor_score:
                direccion = "call" if es_alcista(v) else "put"
                mejor_score = score
                mejor = (par, direccion, score)

        except:
            # Evita que el bot se caiga por un par defectuoso
            continue

    if mejor and mejor_score >= 3:
        return mejor

    return None
