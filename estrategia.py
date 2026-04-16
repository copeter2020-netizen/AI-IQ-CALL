# =========================
# UTILIDADES
# =========================
def cuerpo(v):
    return abs(v["close"] - v["open"])

def rango(v):
    return v["max"] - v["min"]

def es_fuerte(v):
    return cuerpo(v) > (rango(v) * 0.6)

def es_debil(v):
    return cuerpo(v) < (rango(v) * 0.3)

def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# ESTRUCTURA DE MERCADO
# =========================
def estructura_alcista(velas):
    # Higher High + Higher Low
    return (
        velas[-1]["max"] > velas[-3]["max"] and
        velas[-2]["min"] > velas[-4]["min"]
    )

def estructura_bajista(velas):
    # Lower Low + Lower High
    return (
        velas[-1]["min"] < velas[-3]["min"] and
        velas[-2]["max"] < velas[-4]["max"]
    )


# =========================
# LIQUIDEZ (BARRIDAS)
# =========================
def barrida_minimo(velas):
    # rompe mínimo y recupera
    return (
        velas[-2]["min"] < velas[-4]["min"] and
        velas[-2]["close"] > velas[-4]["min"]
    )

def barrida_maximo(velas):
    return (
        velas[-2]["max"] > velas[-4]["max"] and
        velas[-2]["close"] < velas[-4]["max"]
    )


# =========================
# FILTROS AVANZADOS
# =========================
def evitar_rango(velas):
    # evita mercado lateral (sin desplazamiento real)
    rango_total = max(v["max"] for v in velas[-6:]) - min(v["min"] for v in velas[-6:])
    cuerpo_total = sum(cuerpo(v) for v in velas[-6:])
    
    return cuerpo_total > (rango_total * 1.2)


def confirmar_impulso(v):
    # vela institucional real
    return es_fuerte(v) and rango(v) > 0


# =========================
# DETECCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None

    for par, velas in data.items():

        if len(velas) < 15:
            continue

        if not evitar_rango(velas):
            continue  # ❌ evitar mercado muerto

        v_fuerza = velas[-2]
        v_confirm = velas[-1]

        score = 0

        # =========================
        # COMPRA (CALL)
        # =========================
        if estructura_alcista(velas):

            # liquidez
            if barrida_minimo(velas):
                score += 4

            # impulso fuerte
            if confirmar_impulso(v_fuerza) and es_alcista(v_fuerza):
                score += 3

            # continuidad
            if v_confirm["close"] > v_fuerza["close"]:
                score += 2

            # evitar agotamiento
            if es_debil(v_fuerza):
                score -= 3

            if score >= 7:
                if not mejor or score > mejor[2]:
                    mejor = (par, "call", score)

        # =========================
        # VENTA (PUT)
        # =========================
        if estructura_bajista(velas):

            if barrida_maximo(velas):
                score += 4

            if confirmar_impulso(v_fuerza) and es_bajista(v_fuerza):
                score += 3

            if v_confirm["close"] < v_fuerza["close"]:
                score += 2

            if es_debil(v_fuerza):
                score -= 3

            if score >= 7:
                if not mejor or score > mejor[2]:
                    mejor = (par, "put", score)

    return mejor
