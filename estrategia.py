import time

# =========================
# UTILIDADES
# =========================
def body(c):
    return abs(c["close"] - c["open"])

def rango(c):
    return c["max"] - c["min"]

def es_alcista(c):
    return c["close"] > c["open"]

def es_bajista(c):
    return c["close"] < c["open"]

def fuerza(c):
    if rango(c) == 0:
        return 0
    return body(c) / rango(c)

def mecha_superior(c):
    return c["max"] - max(c["open"], c["close"])

def mecha_inferior(c):
    return min(c["open"], c["close"]) - c["min"]


# =========================
# SOPORTE / RESISTENCIA
# =========================
def resistencia(velas):
    return max(v["max"] for v in velas[-15:-1])

def soporte(velas):
    return min(v["min"] for v in velas[-15:-1])


# =========================
# ESTRUCTURA REAL
# =========================
def estructura_alcista(velas):
    return (
        velas[-1]["max"] > velas[-2]["max"] > velas[-3]["max"] and
        velas[-1]["min"] > velas[-2]["min"]
    )

def estructura_bajista(velas):
    return (
        velas[-1]["min"] < velas[-2]["min"] < velas[-3]["min"] and
        velas[-1]["max"] < velas[-2]["max"]
    )


# =========================
# PRESIÓN DEL MERCADO
# =========================
def presion_alcista(velas):
    return sum(es_alcista(v) for v in velas[-5:]) >= 4

def presion_bajista(velas):
    return sum(es_bajista(v) for v in velas[-5:]) >= 4


# =========================
# FILTROS
# =========================
def fake_breakout(v):
    return (
        mecha_superior(v) > body(v) * 1.5 or
        mecha_inferior(v) > body(v) * 1.5
    )

def mercado_lento(velas):
    rangos = [rango(v) for v in velas[-10:]]
    return sum(rangos)/len(rangos) < 0.00005

def continuidad(velas, direccion):
    if direccion == "call":
        return velas[-1]["close"] > velas[-2]["close"]
    else:
        return velas[-1]["close"] < velas[-2]["close"]


# =========================
# PATRÓN
# =========================
def patron_call(v1, v2):
    return es_bajista(v2) and es_alcista(v1) and fuerza(v1) > 0.6

def patron_put(v1, v2):
    return es_alcista(v2) and es_bajista(v1) and fuerza(v1) > 0.6


# =========================
# DETECTOR PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    segundos = int(time.time() % 60)
    if segundos < 55:  # 🔥 precisión timing
        return None

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        if mercado_lento(velas):
            continue

        v1 = velas[-1]
        v2 = velas[-2]

        res = resistencia(velas)
        sop = soporte(velas)

        score = 0
        direccion = None

        # =========================
        # CALL
        # =========================
        if estructura_alcista(velas) and presion_alcista(velas):

            if patron_call(v1, v2):

                if fake_breakout(v1):
                    continue

                if v1["close"] >= res:
                    continue

                if mecha_superior(v1) > body(v1):
                    continue

                if not continuidad(velas, "call"):
                    continue

                # SCORE DINÁMICO
                score += 5  # estructura
                score += 4  # presión
                score += 3  # patrón

                if fuerza(v1) > 0.7:
                    score += 3

                direccion = "call"

        # =========================
        # PUT
        # =========================
        elif estructura_bajista(velas) and presion_bajista(velas):

            if patron_put(v1, v2):

                if fake_breakout(v1):
                    continue

                if v1["close"] <= sop:
                    continue

                if mecha_inferior(v1) > body(v1):
                    continue

                if not continuidad(velas, "put"):
                    continue

                # SCORE DINÁMICO
                score += 5
                score += 4
                score += 3

                if fuerza(v1) > 0.7:
                    score += 3

                direccion = "put"

        # =========================
        # REGLA DE ORO PRO
        # =========================
        if direccion and score >= 14 and score > mejor_score:
            mejor = (par, direccion, score)
            mejor_score = score

    return mejor
