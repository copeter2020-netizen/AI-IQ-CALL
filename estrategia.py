import pandas as pd

# ================================
# 📌 UTILIDADES BÁSICAS
# ================================

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

def cuerpo(v):
    return abs(v["close"] - v["open"])

# ================================
# 📊 DETECCIÓN DE TENDENCIA
# ================================

def tendencia(df):
    ultimas = df.iloc[-10:]
    alcistas = sum(1 for _, v in ultimas.iterrows() if es_alcista(v))
    bajistas = sum(1 for _, v in ultimas.iterrows() if es_bajista(v))

    if alcistas > bajistas:
        return "alcista"
    elif bajistas > alcistas:
        return "bajista"
    return "lateral"

# ================================
# 🔥 ACUMULACIÓN (ANTES DEL MOVIMIENTO)
# ================================

def acumulacion(df):
    velas = df.iloc[-6:]
    cuerpos = [cuerpo(v) for _, v in velas.iterrows()]
    promedio = sum(cuerpos) / len(cuerpos)

    # muchas velas pequeñas = acumulación
    return sum(1 for c in cuerpos if c < promedio) >= 4

# ================================
# ⚠️ EVITAR ENTRADAS TARDÍAS
# ================================

def vela_explosiva(df):
    v = df.iloc[-2]
    media = df["close"].diff().abs().mean()

    return cuerpo(v) > media * 2

# ================================
# 🚀 ENTRADA ANTICIPADA (CLAVE)
# ================================

def entrada_anticipada_compra(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]
    v3 = df.iloc[-4]

    return (
        es_alcista(v1) and
        es_bajista(v2) and
        es_bajista(v3) and
        cuerpo(v1) < cuerpo(v2) * 1.2
    )

def entrada_anticipada_venta(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]
    v3 = df.iloc[-4]

    return (
        es_bajista(v1) and
        es_alcista(v2) and
        es_alcista(v3) and
        cuerpo(v1) < cuerpo(v2) * 1.2
    )

# ================================
# 🔥 MICRO RETROCESO (MÁS ENTRADAS)
# ================================

def micro_pullback_compra(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    return es_alcista(v1) and es_bajista(v2)

def micro_pullback_venta(df):
    v1 = df.iloc[-2]
    v2 = df.iloc[-3]

    return es_bajista(v1) and es_alcista(v2)

# ================================
# 🎯 RSI FILTRO LIGERO (NO BLOQUEA)
# ================================

def rsi_filtro_compra(df):
    if "rsi" not in df.columns:
        return True
    return df.iloc[-2]["rsi"] < 65

def rsi_filtro_venta(df):
    if "rsi" not in df.columns:
        return True
    return df.iloc[-2]["rsi"] > 35

# ================================
# 🧠 FUNCIÓN PRINCIPAL
# ================================

def detectar_entrada(df):
    if len(df) < 20:
        return None

    if vela_explosiva(df):
        return None  # evitar entrar tarde

    t = tendencia(df)

    # ====================
    # 🚀 COMPRA
    # ====================
    if (
        t == "bajista" and
        acumulacion(df) and
        entrada_anticipada_compra(df) and
        rsi_filtro_compra(df)
    ):
        return "CALL"

    # entrada más agresiva (no dejar pasar oportunidades)
    if (
        t == "bajista" and
        micro_pullback_compra(df) and
        rsi_filtro_compra(df)
    ):
        return "CALL"

    # ====================
    # 🚀 VENTA
    # ====================
    if (
        t == "alcista" and
        acumulacion(df) and
        entrada_anticipada_venta(df) and
        rsi_filtro_venta(df)
    ):
        return "PUT"

    # entrada más agresiva
    if (
        t == "alcista" and
        micro_pullback_venta(df) and
        rsi_filtro_venta(df)
    ):
        return "PUT"

    return None
