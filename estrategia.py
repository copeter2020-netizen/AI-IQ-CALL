import statistics

# =========================
# UTILIDADES
# =========================
def cuerpo_vela(v):
    return abs(v["close"] - v["open"])


def es_alcista(v):
    return v["close"] > v["open"]


def es_bajista(v):
    return v["close"] < v["open"]


def promedio_cuerpo(velas):
    cuerpos = [cuerpo_vela(v) for v in velas]
    return statistics.mean(cuerpos)


# =========================
# DETECTAR MOMENTUM REAL
# =========================
def detectar_momentum(velas):
    ultimas = velas[-5:]

    cuerpos = [cuerpo_vela(v) for v in ultimas]
    promedio = statistics.mean(cuerpos)

    fuertes = [c for c in cuerpos if c > promedio * 1.3]

    if len(fuertes) < 3:
        return None

    alcistas = sum(1 for v in ultimas if es_alcista(v))
    bajistas = sum(1 for v in ultimas if es_bajista(v))

    # 🔥 continuidad
    if alcistas >= 4:
        return "call"

    if bajistas >= 4:
        return "put"

    return None


# =========================
# RUPTURA DE ESTRUCTURA
# =========================
def ruptura(velas):
    highs = [v["max"] for v in velas[-10:]]
    lows = [v["min"] for v in velas[-10:]]

    ultimo = velas[-1]

    if ultimo["close"] > max(highs[:-1]):
        return "call"

    if ultimo["close"] < min(lows[:-1]):
        return "put"

    return None


# =========================
# FILTRO ANTI RANGO
# =========================
def mercado_lento(velas):
    rango = max(v["max"] for v in velas[-10:]) - min(v["min"] for v in velas[-10:])
    return rango < 0.0005  # evita lateralidad


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, tf in data.items():

        m1 = tf["m1"]
        m5 = tf["m5"]

        if not m1 or not m5:
            continue

        # 🔥 evitar rango
        if mercado_lento(m1):
            continue

        score = 0

        # =========================
        # MOMENTUM M1
        # =========================
        mom_m1 = detectar_momentum(m1)
        if mom_m1:
            score += 4

        # =========================
        # MOMENTUM M5
        # =========================
        mom_m5 = detectar_momentum(m5)
        if mom_m5:
            score += 3

        # =========================
        # RUPTURA
        # =========================
        romp = ruptura(m1)
        if romp:
            score += 3

        # =========================
        # CONFIRMACIÓN FINAL
        # =========================
        if mom_m1 and mom_m5 and romp:

            direccion = mom_m1

            if score > mejor_score:
                mejor = (par, direccion, score)
                mejor_score = score

    return mejor
