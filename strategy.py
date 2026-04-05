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
# 🔥 ESTRUCTURA REAL
# ==========================
def tendencia_real(df):
    return (
        df["max"].iloc[-1] > df["max"].iloc[-3] and
        df["min"].iloc[-1] > df["min"].iloc[-3]
    ) or (
        df["max"].iloc[-1] < df["max"].iloc[-3] and
        df["min"].iloc[-1] < df["min"].iloc[-3]
    )


# ==========================
# 🔥 FILTROS PRO
# ==========================
def entrada_tardia(df, rango_total):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-4])
    return mov > rango_total * 0.5


def impulso_reciente(df, rango_total):
    mov = df["close"].iloc[-1] - df["close"].iloc[-3]
    return abs(mov) > rango_total * 0.35


def rango_muerto(df):
    velas = df.iloc[-5:]
    return all(body(v) < rango(v) * 0.4 for _, v in velas.iterrows())


def hay_barrida(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return v["min"] < prev["min"] or v["max"] > prev["max"]


def hay_impulso(v):
    return body(v) > rango(v) * 0.5


def vela_fuerte(v):
    return body(v) > rango(v) * 0.6


# ==========================
# 🔥 INTENCIÓN REAL
# ==========================
def rechazo_valido(v, direccion):
    cuerpo = body(v)

    if direccion == "call":
        mecha = mecha_inf(v)
    else:
        mecha = mecha_sup(v)

    return mecha > cuerpo * 1.5


def fallo_continuacion(df, tipo):
    v = df.iloc[-1]
    prev = df.iloc[-2]

    if tipo == "call":
        return v["min"] < prev["min"] and v["close"] > prev["min"]
    else:
        return v["max"] > prev["max"] and v["close"] < prev["max"]


def cierre_fuerte(df, direccion):
    v = df.iloc[-1]

    if direccion == "call":
        return v["close"] > df["max"].iloc[-2]
    else:
        return v["close"] < df["min"].iloc[-2]


def falsa_reversa(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return body(v) < body(prev)


# ==========================
# 🔥 ENTRADA FINAL PRO++
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

        # ==========================
        # FILTROS CRÍTICOS
        # ==========================
        if tendencia_real(df):
            continue

        if entrada_tardia(df, rango_total):
            continue

        if impulso_reciente(df, rango_total):
            continue

        if rango_muerto(df):
            continue

        if falsa_reversa(df):
            continue

        if not hay_barrida(df):
            continue

        if not hay_impulso(v):
            continue

        if not vela_fuerte(v):
            continue

        score = 0
        direccion = None

        div = divergencia_rsi(df)

        # ======================
        # CALL
        # ======================
        if cerca(v["min"], soporte, rango_total):

            if div == "alcista" and rsi_actual < 30:

                if fallo_continuacion(df, "call"):
                    score += 3

                if rechazo_valido(v, "call"):
                    score += 2

                if cierre_fuerte(df, "call"):
                    score += 3

                if es_alcista(v):
                    score += 2

                direccion = "call"

        # ======================
        # PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if div == "bajista" and rsi_actual > 70:

                if fallo_continuacion(df, "put"):
                    score += 3

                if rechazo_valido(v, "put"):
                    score += 2

                if cierre_fuerte(df, "put"):
                    score += 3

                if es_bajista(v):
                    score += 2

                direccion = "put"

        if score > mejor_score and direccion:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 7:
        return mejor

    return None
