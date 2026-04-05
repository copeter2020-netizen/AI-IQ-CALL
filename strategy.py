import pandas as pd
import numpy as np

# ==========================
# UTILIDADES
# ==========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def es_alcista(c):
    return c["close"] > c["open"]

def es_bajista(c):
    return c["close"] < c["open"]


# ==========================
# RSI
# ==========================
def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()

    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


# ==========================
# FILTROS PRO (EVITA MALAS ENTRADAS)
# ==========================
def mercado_lento(df):
    ultimas = df.iloc[-5:]
    return all(body(v) < rango(v) * 0.3 for _, v in ultimas.iterrows())


def tendencia_fuerte(df):
    ultimas = df.iloc[-6:]
    verdes = sum(ultimas["close"] > ultimas["open"])
    rojas = sum(ultimas["close"] < ultimas["open"])
    return verdes >= 5 or rojas >= 5


def sobre_extension(df):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-6])
    rango_total = max(df["max"][-20:]) - min(df["min"][-20:])
    return mov > rango_total * 0.7


def consolidacion(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]
    return np.mean(rangos) < (max(rangos) * 0.5)


def rechazo_valido(v, direccion):
    cuerpo = body(v)

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    if direccion == "call":
        return mecha_inf > cuerpo * 1.5
    else:
        return mecha_sup > cuerpo * 1.5


# ==========================
# NIVELES
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# ENTRADA PRINCIPAL
# ==========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        df["rsi"] = calcular_rsi(df)
        rsi = df["rsi"].iloc[-1]

        soporte, resistencia = niveles(df)
        rango_total = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]

        # ==========================
        # 🔥 FILTROS (EVITAR PERDER)
        # ==========================
        if mercado_lento(df):
            continue

        if tendencia_fuerte(df):
            continue

        if sobre_extension(df):
            continue

        if consolidacion(df):
            continue

        score = 0
        direccion = None

        # ======================
        # CALL
        # ======================
        if abs(v["min"] - soporte) < rango_total * 0.04:

            if rsi < 35:
                score += 2

            if es_alcista(v):
                score += 2

            if body(v) > rango(v) * 0.5:
                score += 2

            if rechazo_valido(v, "call"):
                score += 2

            direccion = "call"

        # ======================
        # PUT
        # ======================
        if abs(v["max"] - resistencia) < rango_total * 0.04:

            if rsi > 65:
                score += 2

            if es_bajista(v):
                score += 2

            if body(v) > rango(v) * 0.5:
                score += 2

            if rechazo_valido(v, "put"):
                score += 2

            direccion = "put"

        # ======================
        # MEJOR SEÑAL
        # ======================
        if score > mejor_score and direccion:
            mejor = (par, direccion, score)
            mejor_score = score

    if mejor and mejor_score >= 5:
        return mejor

    return None
