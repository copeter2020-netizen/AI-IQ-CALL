import pandas as pd
import numpy as np

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

def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def tendencia_fuerte(df):
    ult = df.iloc[-6:]
    verdes = sum(ult["close"] > ult["open"])
    rojas = sum(ult["close"] < ult["open"])
    return verdes >= 5 or rojas >= 5

def consolidacion(df):
    ult = df.iloc[-5:]
    rangos = [rango(v) for _, v in ult.iterrows()]
    return np.mean(rangos) < (max(rangos) * 0.5)

def barrida_liquidez(df):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    return v["max"] > prev["max"] or v["min"] < prev["min"]

def rechazo(v, tipo):
    if tipo == "call":
        return mecha_inf(v) > body(v) * 2
    else:
        return mecha_sup(v) > body(v) * 2

def confirmacion(df, tipo):
    v = df.iloc[-1]
    prev = df.iloc[-2]
    if tipo == "call":
        return v["close"] > prev["max"]
    else:
        return v["close"] < prev["min"]

def divergencia(df):
    precio = df["close"]
    rsi = df["rsi"]

    if precio.iloc[-1] < precio.iloc[-5] and rsi.iloc[-1] > rsi.iloc[-5]:
        return "alcista"

    if precio.iloc[-1] > precio.iloc[-5] and rsi.iloc[-1] < rsi.iloc[-5]:
        return "bajista"

    return None

def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia

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

        if tendencia_fuerte(df):
            continue

        if consolidacion(df):
            continue

        if not barrida_liquidez(df):
            continue

        score = 0
        direccion = None

        div = divergencia(df)

        # CALL
        if abs(v["min"] - soporte) < rango_total * 0.04:
            if div == "alcista" and rsi < 35:
                if rechazo(v, "call"):
                    score += 3
                if confirmacion(df, "call"):
                    score += 3
                if es_alcista(v):
                    score += 2
                direccion = "call"

        # PUT
        if abs(v["max"] - resistencia) < rango_total * 0.04:
            if div == "bajista" and rsi > 65:
                if rechazo(v, "put"):
                    score += 3
                if confirmacion(df, "put"):
                    score += 3
                if es_bajista(v):
                    score += 2
                direccion = "put"

        if score > mejor_score and direccion:
            mejor = (par, direccion, score)
            mejor_score = score

    if mejor and mejor_score >= 6:
        return mejor

    return None
