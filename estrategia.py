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
# 🔥 NUEVA ESTRATEGIA
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 10:
            continue

        df = pd.DataFrame(velas)

        v_indecision = df.iloc[-3]
        v_fuerza = df.iloc[-2]

        # =========================
        # 🟡 INDECISIÓN
        # =========================
        if rango(v_indecision) == 0:
            continue

        cuerpo_ind = body(v_indecision)
        rango_ind = rango(v_indecision)

        es_indecision = cuerpo_ind < (rango_ind * 0.3)

        if not es_indecision:
            continue

        # =========================
        # 💥 FUERZA
        # =========================
        cuerpo_fuerza = body(v_fuerza)
        rango_fuerza = rango(v_fuerza)

        es_fuerza = cuerpo_fuerza > (rango_fuerza * 0.6)

        if not es_fuerza:
            continue

        score = 0

        # =========================
        # 🟢 CALL
        # =========================
        if es_alcista(v_fuerza) and v_fuerza["close"] > v_indecision["max"]:
            score = 10
            mejor = (par, "call", score)

        # =========================
        # 🔴 PUT
        # =========================
        if es_bajista(v_fuerza) and v_fuerza["close"] < v_indecision["min"]:
            score = 10
            mejor = (par, "put", score)

    return mejor
