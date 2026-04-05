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
    return 100 - (100 / (1 + rs))


# ==========================
# NIVELES
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


def cerca(valor, nivel, rango_total):
    return abs(valor - nivel) < rango_total * 0.04


# ==========================
# 🔴 FILTROS CRÍTICOS
# ==========================
def zona_sucia(df, rango_total):
    precio = df["close"].iloc[-1]
    centro = (max(df["max"][-20:]) + min(df["min"][-20:])) / 2
    return abs(precio - centro) < rango_total * 0.2


def mercado_extendido(df, rango_total):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-6])
    return mov > rango_total * 0.6


def tendencia_extrema(df):
    ultimas = df.iloc[-6:]
    bajistas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())
    alcistas = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    return bajistas >= 5 or alcistas >= 5


def entrada_tarde_extrema(df):
    ultimas = df.iloc[-4:]
    bajistas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())
    alcistas = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    return bajistas >= 3 or alcistas >= 3


def rango_muerto(df):
    velas = df.iloc[-5:]
    return all(body(v) < rango(v) * 0.35 for _, v in velas.iterrows())


def posible_trampa(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return (
        body(v) > body(prev) * 1.5 and
        (mecha_sup(v) > body(v) or mecha_inf(v) > body(v))
    )


# ==========================
# 🟢 FILTROS DE PRECISIÓN
# ==========================
def primera_reversa(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]

    return body(v) > body(prev) and (
        (es_alcista(v) and es_bajista(prev)) or
        (es_bajista(v) and es_alcista(prev))
    )


def hay_barrida(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return v["min"] < prev["min"] or v["max"] > prev["max"]


def vela_fuerte(v):
    return body(v) > rango(v) * 0.6


def rechazo_pro(v, direccion):
    cuerpo = body(v)

    if direccion == "call":
        return mecha_inf(v) > cuerpo * 3
    else:
        return mecha_sup(v) > cuerpo * 3


def confirmacion_fuerte(df, direccion):
    v = df.iloc[-1]
    prev = df.iloc[-2]

    if direccion == "call":
        return v["close"] > prev["max"]
    else:
        return v["close"] < prev["min"]


def primer_toque(df, nivel, tipo):
    if tipo == "soporte":
        return df["min"].iloc[-2] > nivel
    else:
        return df["max"].iloc[-2] < nivel


# ==========================
# DIVERGENCIA
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
# 🚀 ENTRADA FINAL
# ==========================
def detectar_entrada_oculta(data_por_par):

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        df["rsi"] = calcular_rsi(df)
        rsi_actual = df["rsi"].iloc[-1]

        soporte, resistencia = niveles(df)
        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]

        # ==========================
        # 🔴 BLOQUEOS TOTALES
        # ==========================
        if zona_sucia(df, rango_total):
            continue

        if mercado_extendido(df, rango_total):
            continue

        if tendencia_extrema(df):
            continue

        if entrada_tarde_extrema(df):
            continue

        if rango_muerto(df):
            continue

        if posible_trampa(df):
            continue

        if not primera_reversa(df):
            continue

        if not hay_barrida(df):
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

            if not primer_toque(df, soporte, "soporte"):
                continue

            if div == "alcista" and rsi_actual < 30:

                if rechazo_pro(v, "call"):
                    score += 2

                if confirmacion_fuerte(df, "call"):
                    score += 3

                if es_alcista(v):
                    score += 2

                direccion = "call"

        # ======================
        # PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if not primer_toque(df, resistencia, "resistencia"):
                continue

            if div == "bajista" and rsi_actual > 70:

                if rechazo_pro(v, "put"):
                    score += 2

                if confirmacion_fuerte(df, "put"):
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
