import pandas as pd

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
# SOPORTE / RESISTENCIA
# ==========================
def niveles(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# RECHAZO (LIQUIDEZ)
# ==========================
def rechazo_soporte(c):
    return mecha_inf(c) > body(c) * 1.5

def rechazo_resistencia(c):
    return mecha_sup(c) > body(c) * 1.5


# ==========================
# CONTINUACIÓN (CONFIRMACIÓN)
# ==========================
def continuidad_alcista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r
    return es_alcista(c) and pos > 0.7 and body(c) > r * 0.5


def continuidad_bajista(c):
    r = rango(c)
    if r == 0:
        return False

    pos = (c["close"] - c["min"]) / r
    return es_bajista(c) and pos < 0.3 and body(c) > r * 0.5


# ==========================
# FUNCIÓN PRINCIPAL
# ==========================
def analyze_market(c1, c5, c15):

    try:
        df = pd.DataFrame(c1)

        if len(df) < 25:
            return None

        soporte, resistencia = niveles(df)

        c1_ = df.iloc[-1]  # confirmación
        c2_ = df.iloc[-2]  # rechazo

        # ==========================
        # 🔥 COMPRA (SOPORTE)
        # ==========================
        if c2_["min"] <= soporte:

            if rechazo_soporte(c2_) and continuidad_alcista(c1_):
                return {
                    "action": "call",
                    "zona": "soporte",
                    "nivel": soporte
                }

        # ==========================
        # 🔥 VENTA (RESISTENCIA)
        # ==========================
        if c2_["max"] >= resistencia:

            if rechazo_resistencia(c2_) and continuidad_bajista(c1_):
                return {
                    "action": "put",
                    "zona": "resistencia",
                    "nivel": resistencia
                }

        return None

    except:
        return None
