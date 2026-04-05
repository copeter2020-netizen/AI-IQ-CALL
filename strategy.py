import pandas as pd
import numpy as np
from filtros import *

def calcular_rsi(df, periodo=14):
    delta = df["close"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(periodo).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(periodo).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 30:
            continue

        df["rsi"] = calcular_rsi(df)
        rsi = df["rsi"].iloc[-1]

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        rango = max(df["max"][-20:]) - min(df["min"][-20:])

        v = df.iloc[-1]
        cuerpo = abs(v["close"] - v["open"])

        # =========================
        # 🔥 FILTROS PRO
        # =========================
        if volatilidad_baja(df): continue
        if mercado_lento(df): continue
        if tendencia_fuerte(df): continue
        if sobre_extension(df): continue
        if mechas_peligrosas(df): continue

        score = 0
        direccion = None

        # =========================
        # CALL
        # =========================
        if abs(v["min"] - soporte) < rango * 0.04:

            if rsi < 30:
                score += 2

            if v["close"] > v["open"]:
                score += 2

            if cuerpo > (v["max"] - v["min"]) * 0.5:
                score += 2

            direccion = "call"

        # =========================
        # PUT
        # =========================
        if abs(v["max"] - resistencia) < rango * 0.04:

            if rsi > 70:
                score += 2

            if v["close"] < v["open"]:
                score += 2

            if cuerpo > (v["max"] - v["min"]) * 0.5:
                score += 2

            direccion = "put"

        if score > mejor_score and direccion:
            mejor = (par, direccion, score)
            mejor_score = score

    if mejor and mejor_score >= 5:
        return mejor

    return None
