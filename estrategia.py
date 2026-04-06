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
# TENDENCIA REAL (NUEVO 🔥)
# =========================
def tendencia_real(df):
    ma20 = df["close"].rolling(20).mean()
    ma50 = df["close"].rolling(50).mean()

    if ma20.iloc[-1] < ma50.iloc[-1]:
        return "bajista"

    if ma20.iloc[-1] > ma50.iloc[-1]:
        return "alcista"

    return "neutral"


# =========================
# NIVELES REALES
# =========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-2]
    resistencia = df["max"].rolling(20).max().iloc[-2]
    return soporte, resistencia


# =========================
# FILTRO LATERAL
# =========================
def mercado_lateral(df):
    ultimas = df.iloc[-6:]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    if len(rangos) == 0:
        return True

    return np.mean(rangos) < (max(rangos) * 0.5)


# =========================
# MICRO TENDENCIA
# =========================
def micro_tendencia(df):
    ultimas = df.iloc[-5:]

    verdes = sum(es_alcista(v) for _, v in ultimas.iterrows())
    rojas = sum(es_bajista(v) for _, v in ultimas.iterrows())

    if verdes >= 4:
        return "alcista"

    if rojas >= 4:
        return "bajista"

    return "neutral"


# =========================
# IMPULSO FUERTE
# =========================
def impulso_fuerte(v):
    if rango(v) == 0:
        return False

    return body(v) > rango(v) * 0.7


# =========================
# RECHAZO FUERTE
# =========================
def rechazo_fuerte(v):
    if rango(v) == 0:
        return False

    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return (
        mecha_sup > body(v) * 1.2 or
        mecha_inf > body(v) * 1.2
    )


# =========================
# VELA REVERSIÓN (NUEVO 🔥)
# =========================
def vela_reversion_alcista(v):
    return (
        es_alcista(v) and
        rechazo_fuerte(v) and
        body(v) > rango(v) * 0.5
    )

def vela_reversion_bajista(v):
    return (
        es_bajista(v) and
        rechazo_fuerte(v) and
        body(v) > rango(v) * 0.5
    )


# =========================
# ZONA MALA
# =========================
def zona_mala(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango_total = resistencia - soporte

    if rango_total == 0:
        return True

    distancia = min(abs(precio - soporte), abs(precio - resistencia))

    return distancia > rango_total * 0.6


# =========================
# ENTRADA TARDE (MEJORADO 🔥)
# =========================
def entrada_tarde(df):
    ultimas = df.iloc[-5:]

    cuerpos = [body(v) for _, v in ultimas.iterrows()]
    rangos = [rango(v) for _, v in ultimas.iterrows()]

    velas_fuertes = sum(c > r * 0.6 for c, r in zip(cuerpos, rangos))

    return velas_fuertes >= 3


# =========================
# RUPTURA FUERTE (NUEVO 🔥)
# =========================
def ruptura_fuerte(df, nivel):
    ultimas = df.iloc[-3:]

    for _, v in ultimas.iterrows():
        if v["close"] < nivel and impulso_fuerte(v):
            return True

    return False


# =========================
# DETECTOR PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 50:
            continue

        df = pd.DataFrame(velas)

        # =========================
        # FILTROS BASE
        # =========================
        if mercado_lateral(df):
            continue

        if entrada_tarde(df):
            continue

        tendencia_macro = tendencia_real(df)
        tendencia_micro = micro_tendencia(df)

        soporte, resistencia = niveles(df)

        if zona_mala(df, soporte, resistencia):
            continue

        v_confirmacion = df.iloc[-2]
        v_manipulacion = df.iloc[-3]

        score = 0

        # =========================
        # SETUP CALL (COMPRA)
        # =========================
        if v_manipulacion["min"] <= soporte:

            # ❌ evitar contra tendencia fuerte
            if tendencia_macro == "bajista":
                continue

            # ❌ evitar ruptura real
            if ruptura_fuerte(df, soporte):
                continue

            # confirmaciones
            if rechazo_fuerte(v_manipulacion):
                score += 2

            if vela_reversion_alcista(v_confirmacion):
                score += 3

            if tendencia_micro == "alcista":
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 2

            if score >= 6:
                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "call", score)

        # =========================
        # SETUP PUT (VENTA)
        # =========================
        if v_manipulacion["max"] >= resistencia:

            # ❌ evitar contra tendencia fuerte
            if tendencia_macro == "alcista":
                continue

            # ❌ evitar ruptura real
            if ruptura_fuerte(df, resistencia):
                continue

            # confirmaciones
            if rechazo_fuerte(v_manipulacion):
                score += 2

            if vela_reversion_bajista(v_confirmacion):
                score += 3

            if tendencia_micro == "bajista":
                score += 2

            if impulso_fuerte(v_confirmacion):
                score += 2

            if score >= 6:
                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, "put", score)

    return mejor
