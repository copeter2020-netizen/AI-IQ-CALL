import pandas as pd
import numpy as np

# ==========================
# 🔥 ESTOCÁSTICO DINAPOLI
# ==========================
def stochastic(df, k_period=8, d_period=3, slowing=3):

    low_min = df["min"].rolling(k_period).min()
    high_max = df["max"].rolling(k_period).max()

    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    k = k.rolling(slowing).mean()
    d = k.rolling(d_period).mean()

    return k, d


# ==========================
# 🔥 UTILIDADES
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
# 🔥 DETECTAR TENDENCIA FUERTE
# ==========================
def tendencia_fuerte(df):

    closes = df["close"].values

    p1 = np.polyfit(range(5), closes[-5:], 1)[0]
    p2 = np.polyfit(range(15), closes[-15:], 1)[0]

    return abs(p1) > abs(p2) and abs(p1) > 0.02


# ==========================
# 🔥 DETECTOR PRINCIPAL
# ==========================
def detectar_mejor_entrada(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 50:
            continue

        soporte, resistencia = niveles(df)
        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]

        r = rango(v)
        if r == 0:
            continue

        c = body(v)
        ms = mecha_sup(v)
        mi = mecha_inf(v)

        # 🚫 BLOQUEO POR TENDENCIA
        if tendencia_fuerte(df):
            continue

        # ==========================
        # 🔥 ESTOCÁSTICO
        # ==========================
        k, d = stochastic(df)

        k1, d1 = k.iloc[-1], d.iloc[-1]
        k2, d2 = k.iloc[-2], d.iloc[-2]

        score = 0
        direccion = None

        # ==========================
        # 🔥 SOPORTE → CALL
        # ==========================
        if abs(v["min"] - soporte) < rango_total * 0.03:

            # 🔥 DINAPOLI EXTREMO
            if k1 > 15:
                continue

            # 🔥 GIRO
            if k2 < d2 and k1 > d1:
                score += 30

            # 🔥 RECHAZO
            if mi > c * 1.5:
                score += 30

            # 🔥 VELA FUERTE
            if es_alcista(v) and c > r * 0.6:
                score += 30

            direccion = "call"

        # ==========================
        # 🔥 RESISTENCIA → PUT
        # ==========================
        elif abs(v["max"] - resistencia) < rango_total * 0.03:

            # 🔥 DINAPOLI EXTREMO
            if k1 < 85:
                continue

            # 🔥 GIRO
            if k2 > d2 and k1 < d1:
                score += 30

            # 🔥 RECHAZO
            if ms > c * 1.5:
                score += 30

            # 🔥 VELA FUERTE
            if es_bajista(v) and c > r * 0.6:
                score += 30

            direccion = "put"

        else:
            continue

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 70:
        return mejor

    return None
