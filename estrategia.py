import pandas as pd

# =========================
# FUNCIONES BASE
# =========================

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

def cuerpo(v):
    return abs(v["close"] - v["open"])

# =========================
# ZONAS (SOPORTE/RESISTENCIA)
# =========================

def calcular_zonas(df, lookback=20):
    resistencia = df["high"].tail(lookback).max()
    soporte = df["low"].tail(lookback).min()
    return soporte, resistencia

def zona_valida(df, soporte, resistencia):
    precio = df["close"].iloc[-1]
    rango = resistencia - soporte

    if rango == 0:
        return False

    # Solo zonas extremas (no zona media)
    return (
        abs(precio - soporte) < rango * 0.25 or
        abs(precio - resistencia) < rango * 0.25
    )

# =========================
# FILTROS DE MERCADO
# =========================

def movimiento_extendido(df, direccion):
    ultimas = df.iloc[-4:]

    if direccion == "call":
        verdes = sum(es_alcista(v) for _, v in ultimas.iterrows())
        return verdes >= 3

    if direccion == "put":
        rojas = sum(es_bajista(v) for _, v in ultimas.iterrows())
        return rojas >= 3

    return False

def frenado(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]
    return cuerpo(v1) < cuerpo(v2)

def zona_acumulacion(df):
    ultimas = df.iloc[-5:]
    cuerpos = [cuerpo(v) for _, v in ultimas.iterrows()]
    promedio = sum(cuerpos) / len(cuerpos)
    return max(cuerpos) < promedio * 1.5

# =========================
# DETECCIÓN DE TENDENCIA
# =========================

def tendencia_bajista(df):
    return df["close"].iloc[-2] < df["close"].iloc[-5]

def tendencia_alcista(df):
    return df["close"].iloc[-2] > df["close"].iloc[-5]

# =========================
# CAMBIO DE COLOR (REVERSAL)
# =========================

def cambio_color_valido(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    return (
        es_alcista(v1) and
        es_bajista(v2) and
        cuerpo(v1) < cuerpo(v2)  # 🔥 frenado
    )

def cambio_color_valido_put(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    return (
        es_bajista(v1) and
        es_alcista(v2) and
        cuerpo(v1) < cuerpo(v2)
    )

# =========================
# MANIPULACIÓN (MECHA)
# =========================

def manipulacion(df):
    v = df.iloc[-2]
    return {
        "min": v["low"],
        "max": v["high"]
    }

# =========================
# FUNCIÓN PRINCIPAL
# =========================

def generar_senal(df, par):

    if len(df) < 30:
        return None

    soporte, resistencia = calcular_zonas(df)

    if not zona_valida(df, soporte, resistencia):
        return None

    zona_manip = manipulacion(df)

    # =========================
    # ENTRADA CALL (REBOTE)
    # =========================

    if (
        tendencia_bajista(df) and
        zona_manip["min"] <= soporte and
        cambio_color_valido(df) and
        zona_acumulacion(df) and
        frenado(df) and
        not movimiento_extendido(df, "call")
    ):
        return {
            "par": par,
            "direccion": "call",
            "expiracion": 1
        }

    # =========================
    # ENTRADA PUT (RECHAZO)
    # =========================

    if (
        tendencia_alcista(df) and
        zona_manip["max"] >= resistencia and
        cambio_color_valido_put(df) and
        zona_acumulacion(df) and
        frenado(df) and
        not movimiento_extendido(df, "put")
    ):
        return {
            "par": par,
            "direccion": "put",
            "expiracion": 1
        }

    return None
