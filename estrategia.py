import numpy as np
import pandas as pd

# =========================
# UTILIDADES
# =========================
def body(v):
    return abs(v["close"] - v["open"])

def rango(v):
    return v["max"] - v["min"]

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

# =========================
# INDICADORES
# =========================
def calcular_rsi(df, periodos=14):
    delta = df["close"].diff()
    subida = delta.clip(lower=0)
    bajada = -1 * delta.clip(upper=0)

    media_subida = subida.rolling(periodos).mean()
    media_bajada = bajada.rolling(periodos).mean()

    rs = media_subida / media_bajada
    rsi = 100 - (100 / (1 + rs))

    return rsi

# =========================
# DETECCIÓN DE SEÑAL
# =========================
def detectar_entrada(df):
    if len(df) < 20:
        return None

    df["rsi"] = calcular_rsi(df)

    ultima = df.iloc[-1]
    anterior = df.iloc[-2]

    score = 0
    direccion = None

    # =========================
    # CONDICIONES DE COMPRA (CALL)
    # =========================
    if es_alcista(ultima):
        score += 2

    if ultima["rsi"] < 30:
        score += 2

    if body(ultima) > body(anterior):
        score += 1

    if score >= 4:
        direccion = "call"

    # =========================
    # CONDICIONES DE VENTA (PUT)
    # =========================
    score_put = 0

    if es_bajista(ultima):
        score_put += 2

    if ultima["rsi"] > 70:
        score_put += 2

    if body(ultima) > body(anterior):
        score_put += 1

    if score_put > score:
        score = score_put
        direccion = "put"

    if direccion:
        return {
            "direccion": direccion,
            "score": score
        }

    return None

# =========================
# FUNCIÓN PRINCIPAL
# =========================
def detectar_mejor_entrada(lista_pares, obtener_velas):
    """
    lista_pares: lista de activos
    obtener_velas: función que devuelve dataframe de velas
    """

    mejor = None

    for par in lista_pares:
        try:
            df = obtener_velas(par)

            if df is None or df.empty:
                continue

            señal = detectar_entrada(df)

            if señal:
                print(f"📊 Señal {par} {señal['direccion'].upper()} Score:{señal['score']}")

                if (mejor is None) or (señal["score"] > mejor["score"]):
                    mejor = {
                        "par": par,
                        "direccion": señal["direccion"],
                        "score": señal["score"]
                    }

        except Exception as e:
            continue

    return mejor
