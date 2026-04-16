import time

# =========================
# CONFIG
# =========================
MAX_OPERACIONES_DIA = 2
operaciones_hoy = 0
ultimo_reset = time.strftime("%Y-%m-%d")


# =========================
# RESET DIARIO
# =========================
def reset_dia():
    global operaciones_hoy, ultimo_reset

    hoy = time.strftime("%Y-%m-%d")

    if hoy != ultimo_reset:
        operaciones_hoy = 0
        ultimo_reset = hoy


# =========================
# DETECTAR TENDENCIA
# =========================
def detectar_tendencia(velas):
    closes = [v["close"] for v in velas[-10:]]

    if closes[-1] > closes[0]:
        return "alcista"
    elif closes[-1] < closes[0]:
        return "bajista"
    else:
        return None


# =========================
# VELA FUERTE
# =========================
def es_vela_fuerte(v):
    cuerpo = abs(v["close"] - v["open"])
    rango = v["max"] - v["min"]

    if rango == 0:
        return False

    return cuerpo > (rango * 0.7)


# =========================
# EVITAR AGOTAMIENTO
# =========================
def hay_agotamiento(v):
    cuerpo = abs(v["close"] - v["open"])
    mecha_sup = v["max"] - max(v["close"], v["open"])
    mecha_inf = min(v["close"], v["open"]) - v["min"]

    return mecha_sup > cuerpo or mecha_inf > cuerpo


# =========================
# SOPORTE / RESISTENCIA SIMPLE
# =========================
def cerca_soporte_resistencia(velas):
    maximo = max(v["max"] for v in velas[-15:])
    minimo = min(v["min"] for v in velas[-15:])
    actual = velas[-1]["close"]

    margen = (maximo - minimo) * 0.1

    if abs(actual - maximo) < margen:
        return True

    if abs(actual - minimo) < margen:
        return True

    return False


# =========================
# PATRÓN CONTINUIDAD
# =========================
def patron_continuidad(velas, tendencia):
    v1, v2, v3 = velas[-3:]

    if tendencia == "alcista":
        return (
            v1["close"] < v1["open"] and  # retroceso
            es_vela_fuerte(v2) and v2["close"] > v2["open"] and
            v3["close"] > v2["close"]
        )

    if tendencia == "bajista":
        return (
            v1["close"] > v1["open"] and
            es_vela_fuerte(v2) and v2["close"] < v2["open"] and
            v3["close"] < v2["close"]
        )

    return False


# =========================
# SCORE (FILTRO PREMIUM)
# =========================
def calcular_score(velas, tendencia):
    score = 0

    v2 = velas[-2]

    if es_vela_fuerte(v2):
        score += 4

    if not hay_agotamiento(v2):
        score += 3

    if not cerca_soporte_resistencia(velas):
        score += 3

    if patron_continuidad(velas, tendencia):
        score += 5

    return score


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):
    global operaciones_hoy

    reset_dia()

    if operaciones_hoy >= MAX_OPERACIONES_DIA:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        tendencia = detectar_tendencia(velas)

        if not tendencia:
            continue

        score = calcular_score(velas, tendencia)

        if score >= 10:  # 🔥 SOLO ENTRADAS TOP

            direccion = "call" if tendencia == "alcista" else "put"

            if score > mejor_score:
                mejor_score = score
                mejor = (par, direccion, score)

    if mejor:
        operaciones_hoy += 1

    return mejor
