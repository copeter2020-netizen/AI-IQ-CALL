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
# 🔥 VALIDACIONES
# =========================
def es_indecision(v):
    if rango(v) == 0:
        return False

    return body(v) < (rango(v) * 0.3)


def es_fuerza(v):
    if rango(v) == 0:
        return False

    return body(v) > (rango(v) * 0.6)


def ruptura_alcista(v_fuerza, v_indecision):
    return v_fuerza["close"] > v_indecision["max"]


def ruptura_bajista(v_fuerza, v_indecision):
    return v_fuerza["close"] < v_indecision["min"]


def diferencia_clara(v1, v2):
    return body(v2) > body(v1) * 1.5


# =========================
# 🔥 ESTRATEGIA PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 10:
            continue

        df = pd.DataFrame(velas)

        v_ind = df.iloc[-3]
        v_fuerza = df.iloc[-2]

        # =========================
        # 🟡 INDECISIÓN REAL
        # =========================
        if not es_indecision(v_ind):
            continue

        # =========================
        # 💥 FUERZA REAL
        # =========================
        if not es_fuerza(v_fuerza):
            continue

        # =========================
        # 🔥 DIFERENCIA CLARA
        # =========================
        if not diferencia_clara(v_ind, v_fuerza):
            continue

        score = 0

        # =========================
        # 🟢 CALL
        # =========================
        if es_alcista(v_fuerza) and ruptura_alcista(v_fuerza, v_ind):
            score += 10

        # =========================
        # 🔴 PUT
        # =========================
        elif es_bajista(v_fuerza) and ruptura_bajista(v_fuerza, v_ind):
            score += 10

        else:
            continue

        # =========================
        # FILTRO FINAL
        # =========================
        if score >= 10 and score > mejor_score:
            mejor_score = score
            mejor = (par, "call" if es_alcista(v_fuerza) else "put", score)

    return mejor
