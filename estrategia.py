import pandas as pd


def body(v):
    return abs(v["close"] - v["open"])


def rango(v):
    return v["max"] - v["min"]


def es_alcista(v):
    return v["close"] > v["open"]


def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# MECHAS
# =========================
def mecha_superior(v):
    return v["max"] - max(v["open"], v["close"])


def mecha_inferior(v):
    return min(v["open"], v["close"]) - v["min"]


# =========================
# ZONAS (SOPORTE / RESISTENCIA)
# =========================
def niveles(df):
    resistencia = df["max"].rolling(20).max().iloc[-2]
    soporte = df["min"].rolling(20).min().iloc[-2]
    return soporte, resistencia


# =========================
# TENDENCIA CORTA
# =========================
def tendencia_corta(df):
    ultimas = df.iloc[-5:]

    verdes = sum(v["close"] > v["open"] for _, v in ultimas.iterrows())
    rojas = sum(v["close"] < v["open"] for _, v in ultimas.iterrows())

    if verdes >= 3:
        return "alcista"
    if rojas >= 3:
        return "bajista"

    return "neutral"


# =========================
# VALIDACIONES
# =========================
def vela_fuerte(v):
    if rango(v) == 0:
        return False
    return body(v) > rango(v) * 0.5


def rechazo_superior(v):
    return mecha_superior(v) > body(v) * 1.2


def rechazo_inferior(v):
    return mecha_inferior(v) > body(v) * 1.2


# =========================
# ESTRATEGIA PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 25:
            continue

        df = pd.DataFrame(velas)

        soporte, resistencia = niveles(df)
        tendencia = tendencia_corta(df)

        v_fake = df.iloc[-2]   # vela de ruptura falsa
        v_conf = df.iloc[-1]   # vela confirmación

        score = 0

        # =========================
        # 🔴 PUT (FAKE BREAKOUT ARRIBA)
        # =========================
        if tendencia == "alcista":

            # rompe resistencia
            if v_fake["max"] >= resistencia:

                # cierra debajo (fake breakout)
                if v_fake["close"] < resistencia:

                    # rechazo fuerte
                    if rechazo_superior(v_fake):
                        score += 4

                    # confirmación bajista
                    if es_bajista(v_conf) and vela_fuerte(v_conf):
                        score += 6

                    if score >= 8 and score > mejor_score:
                        mejor_score = score
                        mejor = (par, "put", score)

        # =========================
        # 🟢 CALL (FAKE BREAKOUT ABAJO)
        # =========================
        if tendencia == "bajista":

            # rompe soporte
            if v_fake["min"] <= soporte:

                # cierra arriba (fake)
                if v_fake["close"] > soporte:

                    # rechazo inferior
                    if rechazo_inferior(v_fake):
                        score += 4

                    # confirmación alcista
                    if es_alcista(v_conf) and vela_fuerte(v_conf):
                        score += 6

                    if score >= 8 and score > mejor_score:
                        mejor_score = score
                        mejor = (par, "call", score)

    return mejor
