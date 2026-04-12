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
# VALIDACIONES
# =========================
def es_indecision(v):
    if rango(v) == 0:
        return False
    return body(v) < (rango(v) * 0.3)


def es_fuerza(v):
    if rango(v) == 0:
        return False
    return body(v) > (rango(v) * 0.6)


def es_continuidad_alcista(v):
    return es_alcista(v) and body(v) > rango(v) * 0.4


def es_continuidad_bajista(v):
    return es_bajista(v) and body(v) > rango(v) * 0.4


# =========================
# ESTRATEGIA FORZADA
# =========================
def detectar_entrada_oculta(data):

    for par, velas in data.items():

        if len(velas) < 10:
            continue

        df = pd.DataFrame(velas)

        v_ind = df.iloc[-4]
        v_fuerza = df.iloc[-3]
        v_cont = df.iloc[-2]

        # =========================
        # 1. INDECISIÓN
        # =========================
        if not es_indecision(v_ind):
            continue

        # =========================
        # 2. FUERZA + RUPTURA
        # =========================
        if not es_fuerza(v_fuerza):
            continue

        ruptura_alcista = v_fuerza["close"] > v_ind["max"]
        ruptura_bajista = v_fuerza["close"] < v_ind["min"]

        if not (ruptura_alcista or ruptura_bajista):
            continue

        # =========================
        # 3. CONTINUIDAD OBLIGATORIA
        # =========================
        # CALL
        if ruptura_alcista:
            if not es_continuidad_alcista(v_cont):
                continue
            if v_cont["close"] <= v_fuerza["close"]:
                continue

            return (par, "call", 10)

        # PUT
        if ruptura_bajista:
            if not es_continuidad_bajista(v_cont):
                continue
            if v_cont["close"] >= v_fuerza["close"]:
                continue

            return (par, "put", 10)

    return None
