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
# 🔒 DIVERGENCIA + NIVEL
# ==========================
def detectar_divergencia_nivel(df):
    if len(df) < 20:
        return None, None

    precios = df["close"]
    rsi = df["rsi"]

    # Divergencia alcista → guardar mínimo
    if precios.iloc[-1] < precios.iloc[-5] and rsi.iloc[-1] > rsi.iloc[-5]:
        nivel = df["min"].iloc[-1]
        return "alcista", nivel

    # Divergencia bajista → guardar máximo
    if precios.iloc[-1] > precios.iloc[-5] and rsi.iloc[-1] < rsi.iloc[-5]:
        nivel = df["max"].iloc[-1]
        return "bajista", nivel

    return None, None


# ==========================
# 🔁 RETESTEO DE DIVERGENCIA
# ==========================
def retesteo_divergencia(v, nivel, tipo, rango_total):
    if nivel is None:
        return False

    if tipo == "alcista":
        return abs(v["min"] - nivel) < rango_total * 0.02
    else:
        return abs(v["max"] - nivel) < rango_total * 0.02


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

    return body(v2) < body(v1) and body(v3) > body(v2)


# ==========================
# 🔥 ENTRADA PRO (MODIFICADA)
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

        div_tipo, div_nivel = detectar_divergencia_nivel(df)

        # ======================
        # 🔥 CALL (OBLIGATORIO)
        # ======================
        if div_tipo == "alcista":

            if retesteo_divergencia(v, div_nivel, "alcista", rango_total):

                if rsi_actual < 30:
                    score += 3

                    if fake_breakout(v, div_nivel, "soporte"):
                        score += 2

                    if micro_retroceso(df):
                        score += 1

                    if mecha_inf(v) > body(v):
                        score += 2

                    if es_alcista(v):
                        score += 2

                    direccion = "call"

        # ======================
        # 🔥 PUT (OBLIGATORIO)
        # ======================
        if div_tipo == "bajista":

            if retesteo_divergencia(v, div_nivel, "bajista", rango_total):

                if rsi_actual > 70:
                    score += 3

                    if fake_breakout(v, div_nivel, "resistencia"):
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
