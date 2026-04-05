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
# RSI DIVERGENCIA
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
# 🔥 FILTROS PRO AVANZADOS
# ==========================

def zona_peligrosa(df, rango_total):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-5])
    return mov > rango_total * 0.6


def mercado_estirado(df, rango_total):
    mov = df["close"].iloc[-1] - df["close"].iloc[-6]
    return abs(mov) > rango_total * 0.55


def entrada_tardia(df, rango_total):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-4])
    return mov > rango_total * 0.5


def impulso_reciente(df, rango_total):
    mov = df["close"].iloc[-1] - df["close"].iloc[-3]
    return abs(mov) > rango_total * 0.35


def rango_muerto(df):
    velas = df.iloc[-5:]
    return all(body(v) < rango(v) * 0.4 for _, v in velas.iterrows())


def posible_trampa(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]

    return (
        body(v) > body(prev) * 1.5 and
        (mecha_sup(v) > body(v) or mecha_inf(v) > body(v))
    )


def secuencia_fuerte(df):
    ultimas = df.iloc[-5:]
    verdes = sum(ultimas["close"] > ultimas["open"])
    rojas = sum(ultimas["close"] < ultimas["open"])
    return verdes >= 4 or rojas >= 4


def sobrecompra(rsi):
    return rsi > 65


def sobreventa(rsi):
    return rsi < 35


def zona_extrema(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango = resistencia - soporte

    cerca_res = abs(precio - resistencia) < rango * 0.1
    cerca_sup = abs(precio - soporte) < rango * 0.1

    return cerca_res, cerca_sup


def vela_agotamiento(v):
    return (
        body(v) > rango(v) * 0.6 and
        (mecha_sup(v) > body(v) * 0.5 or mecha_inf(v) > body(v) * 0.5)
    )


# ==========================
# ACCIÓN DE PRECIO
# ==========================
def hay_barrida(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return v["min"] < prev["min"] or v["max"] > prev["max"]


def hay_impulso(v):
    return body(v) > rango(v) * 0.5


def vela_fuerte(v):
    return body(v) > rango(v) * 0.6


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


def cierre_confirmado(df, direccion):
    v = df.iloc[-1]

    if direccion == "call":
        return v["close"] > df["max"].iloc[-2] and body(v) > rango(v) * 0.5
    else:
        return v["close"] < df["min"].iloc[-2] and body(v) > rango(v) * 0.5


# ==========================
# 🎯 ENTRADA FINAL SNIPER PRO
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
        if zona_peligrosa(df, rango_total):
            continue

        if mercado_estirado(df, rango_total):
            continue

        if entrada_tardia(df, rango_total):
            continue

        if impulso_reciente(df, rango_total):
            continue

        if rango_muerto(df):
            continue

        if posible_trampa(df):
            continue

        if secuencia_fuerte(df):
            continue

        if vela_agotamiento(v):
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

        cerca_res, cerca_sup = zona_extrema(df, soporte, resistencia)

        # ======================
        # CALL
        # ======================
        if cerca(v["min"], soporte, rango_total):

            if div == "alcista" and rsi_actual < 30:

                if sobrecompra(rsi_actual):
                    continue

                if cerca_res:
                    continue

                if fallo_continuacion(df, "call"):
                    score += 3

                if rechazo_valido(v, "call"):
                    score += 2

                if cierre_confirmado(df, "call"):
                    score += 3

                if es_alcista(v):
                    score += 2

                direccion = "call"

        # ======================
        # PUT
        # ======================
        if cerca(v["max"], resistencia, rango_total):

            if div == "bajista" and rsi_actual > 70:

                if sobreventa(rsi_actual):
                    continue

                if cerca_sup:
                    continue

                if fallo_continuacion(df, "put"):
                    score += 3

                if rechazo_valido(v, "put"):
                    score += 2

                if cierre_confirmado(df, "put"):
                    score += 3

                if es_bajista(v):
                    score += 2

                direccion = "put"

        if score > mejor_score and direccion:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 8:
        return mejor

    return None
