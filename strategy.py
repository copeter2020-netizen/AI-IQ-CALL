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
# RSI
# ==========================
def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()

    ganancia = np.where(delta > 0, delta, 0)
    perdida = np.where(delta < 0, -delta, 0)

    roll_up = pd.Series(ganancia).rolling(periodo).mean()
    roll_down = pd.Series(perdida).rolling(periodo).mean()

    rs = roll_up / roll_down
    rsi = 100 - (100 / (1 + rs))

    return rsi


# ==========================
# SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# CERCA DE ZONA
# ==========================
def cerca(valor, nivel, rango_total):
    return abs(valor - nivel) < rango_total * 0.05


# ==========================
# MERCADO ACTIVO
# ==========================
def mercado_activo(df):
    highs = df["max"].values
    lows = df["min"].values

    vol = np.mean(highs[-5:] - lows[-5:])
    rango_total = max(highs[-20:]) - min(lows[-20:])

    return rango_total > vol * 2


# ==========================
# 🔒 DIVERGENCIA RSI
# ==========================
def divergencia_rsi(df):
    if len(df) < 20:
        return None

    precios = df["close"]
    rsi = df["rsi"]

    # mínimos
    if precios.iloc[-1] < precios.iloc[-5] and rsi.iloc[-1] > rsi.iloc[-5]:
        return "alcista"

    # máximos
    if precios.iloc[-1] > precios.iloc[-5] and rsi.iloc[-1] < rsi.iloc[-5]:
        return "bajista"

    return None


# ==========================
# 🧠 FAKE BREAKOUT
# ==========================
def fake_breakout(v, nivel, tipo="soporte"):
    if tipo == "soporte":
        return v["min"] < nivel and v["close"] > nivel
    else:
        return v["max"] > nivel and v["close"] < nivel


# ==========================
# 🎯 MICRO RETROCESO
# ==========================
def micro_retroceso(df):
    if len(df) < 3:
        return False

    v1 = df.iloc[-3]
    v2 = df.iloc[-2]
    v3 = df.iloc[-1]

    # pequeño retroceso antes de impulso
    return body(v2) < body(v1) and body(v3) > body(v2)


# ==========================
# 🔥 ENTRADA PRO
# ==========================
def detectar_entrada_oculta(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        if not mercado_activo(df):
            continue

        df["rsi"] = calcular_rsi(df)
        rsi_actual = df["rsi"].iloc[-1]

        soporte, resistencia = niveles(df)
        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]

        score = 0
        direccion = None

        div = divergencia_rsi(df)

        # ======================
        # 🔥 CALL
        # ======================
        if cerca(v["min"], soporte, rango_total):

            if rsi_actual < 30:
                score += 2
                if rsi_actual < 25:
                    score += 1
                if rsi_actual < 20:
                    score += 1

            if div == "alcista":
                score += 2

            if fake_breakout(v, soporte, "soporte"):
                score += 2

            if micro_retroceso(df):
                score += 1

            if mecha_inf(v) > body(v):
                score += 2

            if es_alcista(v):
                score += 2

            direccion = "call"

        # ======================
        # 🔥 PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if rsi_actual > 70:
                score += 2
                if rsi_actual > 75:
                    score += 1
                if rsi_actual > 80:
                    score += 1

            if div == "bajista":
                score += 2

            if fake_breakout(v, resistencia, "resistencia"):
                score += 2

            if micro_retroceso(df):
                score += 1

            if mecha_sup(v) > body(v):
                score += 2

            if es_bajista(v):
                score += 2

            direccion = "put"

        if score > mejor_score and direccion:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 5:
        return mejor

    return None
