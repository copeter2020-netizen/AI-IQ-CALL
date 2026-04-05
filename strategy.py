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
# 🔒 DIVERGENCIA
# ==========================
def divergencia_rsi(df):
    precios = df["close"]
    rsi = df["rsi"]

    if precios.iloc[-1] < precios.iloc[-5] and rsi.iloc[-1] > rsi.iloc[-5]:
        return "alcista"

    if precios.iloc[-1] > precios.iloc[-5] and rsi.iloc[-1] < rsi.iloc[-5]:
        return "bajista"

    return None


# ==========================
# 🧠 FAKE BREAKOUT
# ==========================
def fake_breakout(v, nivel, tipo):
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
# 🔥 VELA TRAMPA
# ==========================
def vela_trampa(v):
    return (
        body(v) < rango(v) * 0.4 and
        (mecha_inf(v) > body(v) or mecha_sup(v) > body(v))
    )


# ==========================
# 🔥 BARRIDA
# ==========================
def hay_barrida(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return v["min"] < prev["min"] or v["max"] > prev["max"]


# ==========================
# 🔥 LATERAL
# ==========================
def mercado_lateral(df, rango_total):
    velas = df.iloc[-5:]
    rango_prom = np.mean(velas["max"] - velas["min"])
    return rango_prom < rango_total * 0.2


# ==========================
# 🔥 IMPULSO
# ==========================
def hay_impulso(v):
    return body(v) > rango(v) * 0.5


# ==========================
# 🔥 FILTRO TENDENCIA FUERTE
# ==========================
def tendencia_fuerte(df):
    ultimas = df.iloc[-4:]
    alcistas = sum(ultimas["close"] > ultimas["open"])
    bajistas = sum(ultimas["close"] < ultimas["open"])

    return alcistas == 4 or bajistas == 4


# ==========================
# 🔥 FILTRO AGOTAMIENTO
# ==========================
def hay_agotamiento(df):
    velas = df.iloc[-3:]
    return all(body(v) < rango(v) * 0.5 for _, v in velas.iterrows())


# ==========================
# 🔥 SOBREEXTENSIÓN
# ==========================
def sobre_extension(df, rango_total):
    mov = df["close"].iloc[-1] - df["close"].iloc[-5]
    return abs(mov) > rango_total * 0.4


# ==========================
# 🔥 ENTRADA FINAL PRO
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
        prev = df.iloc[-2]

        # ❌ filtros duros
        if mercado_lateral(df, rango_total):
            continue

        if not hay_barrida(df):
            continue

        if not hay_impulso(v):
            continue

        if tendencia_fuerte(df):
            continue

        if not hay_agotamiento(df):
            continue

        if sobre_extension(df, rango_total):
            continue

        score = 0
        direccion = None

        div = divergencia_rsi(df)

        # ======================
        # CALL
        # ======================
        if cerca(v["min"], soporte, rango_total):

            if div == "alcista" and rsi_actual < 30:

                if vela_trampa(prev):
                    score += 3

                if fake_breakout(prev, soporte, "soporte"):
                    score += 2

                if micro_retroceso(df):
                    score += 1

                if es_alcista(v):  # confirmación giro
                    score += 2

                direccion = "call"

        # ======================
        # PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if div == "bajista" and rsi_actual > 70:

                if vela_trampa(prev):
                    score += 3

                if fake_breakout(prev, resistencia, "resistencia"):
                    score += 2

                if micro_retroceso(df):
                    score += 1

                if es_bajista(v):  # confirmación giro
                    score += 2

                direccion = "put"

        if score > mejor_score and direccion:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 6:
        return mejor

    return None
