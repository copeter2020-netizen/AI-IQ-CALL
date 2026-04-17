# =========================
# UTILIDADES
# =========================
def es_alcista(v):
    return v["close"] > v["open"]

def es_bajista(v):
    return v["close"] < v["open"]

def cuerpo(v):
    return abs(v["close"] - v["open"])

def mecha_superior(v):
    return v["max"] - max(v["open"], v["close"])

def mecha_inferior(v):
    return min(v["open"], v["close"]) - v["min"]


# =========================
# RSI
# =========================
def calcular_rsi(velas, periodo=14):
    cierres = [v["close"] for v in velas]

    ganancias, perdidas = [], []

    for i in range(1, len(cierres)):
        cambio = cierres[i] - cierres[i - 1]
        if cambio > 0:
            ganancias.append(cambio)
            perdidas.append(0)
        else:
            ganancias.append(0)
            perdidas.append(abs(cambio))

    if len(ganancias) < periodo:
        return 35

    avg_gain = sum(ganancias[-periodo:]) / periodo
    avg_loss = sum(perdidas[-periodo:]) / periodo

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# =========================
# BOLLINGER
# =========================
def calcular_bollinger(velas, periodo=20):
    cierres = [v["close"] for v in velas[-periodo:]]

    if len(cierres) < periodo:
        return None, None, None

    media = sum(cierres) / periodo
    varianza = sum((c - media) ** 2 for c in cierres) / periodo
    desviacion = varianza ** 0.5

    upper = media + (2 * desviacion)
    lower = media - (2 * desviacion)

    return upper, media, lower


# =========================
# TENDENCIA
# =========================
def detectar_tendencia(velas):
    highs = [v["max"] for v in velas[-10:]]
    lows = [v["min"] for v in velas[-10:]]

    if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
        return "alcista"

    if highs[-1] < highs[-2] and lows[-1] < lows[-2]:
        return "bajista"

    return None


# =========================
# SOPORTE / RESISTENCIA
# =========================
def detectar_zona(velas):
    zona_alta = max(v["max"] for v in velas[-15:])
    zona_baja = min(v["min"] for v in velas[-15:])
    return zona_alta, zona_baja


# =========================
# ESTRATEGIA 1: ENTRADA OCULTA
# =========================
def entrada_oculta(velas, tendencia):
    v1, v2 = velas[-3], velas[-2]
    score = 0

    if tendencia == "alcista":
        if es_bajista(v1) and es_alcista(v2):
            score += 4
            return ("call", score)

    if tendencia == "bajista":
        if es_alcista(v1) and es_bajista(v2):
            score += 4
            return ("put", score)

    return None


# =========================
# ESTRATEGIA 2: RECHAZO EN ZONA
# =========================
def rechazo_zona(velas, tendencia):
    ultima = velas[-2]
    zona_alta, zona_baja = detectar_zona(velas)
    score = 0

    if tendencia == "alcista":
        if ultima["min"] <= zona_baja:
            if mecha_inferior(ultima) > cuerpo(ultima) * 1.5:
                if es_alcista(ultima):
                    score += 4
                    return ("call", score)

    if tendencia == "bajista":
        if ultima["max"] >= zona_alta:
            if mecha_superior(ultima) > cuerpo(ultima) * 1.5:
                if es_bajista(ultima):
                    score += 4
                    return ("put", score)

    return None


# =========================
# ESTRATEGIA 3: RUPTURA
# =========================
def ruptura_continuidad(velas, tendencia):
    v1, v2 = velas[-3], velas[-2]
    score = 0

    if tendencia == "alcista":
        if v2["close"] > v1["max"] and es_alcista(v2):
            score += 4
            return ("call", score)

    if tendencia == "bajista":
        if v2["close"] < v1["min"] and es_bajista(v2):
            score += 4
            return ("put", score)

    return None


# =========================
# ESTRATEGIA 4: MULTI-TEMPORAL
# =========================
def confirmacion_multitemporal(velas_m1, velas_m5, tendencia):

    rsi_m1 = calcular_rsi(velas_m1)
    rsi_m5 = calcular_rsi(velas_m5)

    upper, media, lower = calcular_bollinger(velas_m1)

    if upper is None:
        return None

    ultima = velas_m1[-2]
    score = 0

    if tendencia == "alcista":
        if rsi_m1 > 35 and rsi_m5 > 35:
            score += 4

            if ultima["close"] <= media or ultima["min"] <= lower:
                score += 4

            if es_alcista(ultima):
                score += 4

            if score >= 7:
                return ("call", score)

    if tendencia == "bajista":
        if rsi_m1 < 35 and rsi_m5 < 35:
            score += 4

            if ultima["close"] >= media or ultima["max"] >= upper:
                score += 4

            if es_bajista(ultima):
                score += 4

            if score >= 4:
                return ("put", score)

    return None


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    for par in data:

        velas_m1 = data[par]["m1"]
        velas_m5 = data[par]["m5"]

        if len(velas_m1) < 20 or len(velas_m5) < 20:
            continue

        tendencia = detectar_tendencia(velas_m1)

        if not tendencia:
            continue

        señales = []

        e1 = entrada_oculta(velas_m1, tendencia)
        if e1:
            señales.append(e1)

        e2 = rechazo_zona(velas_m1, tendencia)
        if e2:
            señales.append(e2)

        e3 = ruptura_continuidad(velas_m1, tendencia)
        if e3:
            señales.append(e3)

        e4 = confirmacion_multitemporal(velas_m1, velas_m5, tendencia)
        if e4:
            señales.append(e4)

        if señales:
            mejor = max(señales, key=lambda x: x[1])
            direccion, score = mejor

            if score >= 4:
                return par, direccion, score

    return None
