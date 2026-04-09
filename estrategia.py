import pandas as pd


# =========================
# IMPULSO FUERTE
# =========================
def impulso_fuerte(v):
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    cuerpo = abs(v["close"] - v["open"])

    return cuerpo > (rango * 0.7)


# =========================
# CONTINUIDAD
# =========================
def continuidad(df):

    ultimas = df.iloc[-4:]

    alcistas = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    bajistas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())

    if alcistas >= 3:
        return "alcista"

    if bajistas >= 3:
        return "bajista"

    return "neutral"


# =========================
# FUERZA DEL MOVIMIENTO
# =========================
def fuerza(df):
    v = df.iloc[-2]

    rango = v["max"] - v["min"]

    if rango == 0:
        return 0

    cuerpo = abs(v["close"] - v["open"])

    return cuerpo / rango


# =========================
# MAIN
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par in ["EURUSD", "EURJPY"]:

        velas = data.get(par, [])

        if len(velas) < 20:
            continue

        df = pd.DataFrame(velas)

        direccion = continuidad(df)

        if direccion == "neutral":
            continue

        v = df.iloc[-2]

        # SOLO SI HAY IMPULSO REAL
        if not impulso_fuerte(v):
            continue

        score = fuerza(df)

        if score > mejor_score:
            mejor_score = score

            if direccion == "alcista":
                mejor = (par, "call", score)
            else:
                mejor = (par, "put", score)

    return mejor
