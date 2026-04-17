# =========================
# UTILIDADES
# =========================
def cuerpo(v):
    return abs(v["close"] - v["open"])


def mecha_superior(v):
    return v["max"] - max(v["open"], v["close"])


def mecha_inferior(v):
    return min(v["open"], v["close"]) - v["min"]


def es_alcista(v):
    return v["close"] > v["open"]


def es_bajista(v):
    return v["close"] < v["open"]


# =========================
# DETECTAR TENDENCIA FUERTE
# =========================
def tendencia_fuerte(velas):
    ultimas = velas[-5:]

    alcistas = sum(1 for v in ultimas if es_alcista(v))
    bajistas = sum(1 for v in ultimas if es_bajista(v))

    if alcistas >= 4:
        return "call"

    if bajistas >= 4:
        return "put"

    return None


# =========================
# CONTINUIDAD REAL
# =========================
def continuidad(velas, direccion):
    ultimas = velas[-3:]

    if direccion == "call":
        return all(es_alcista(v) for v in ultimas)

    if direccion == "put":
        return all(es_bajista(v) for v in ultimas)

    return False


# =========================
# BLOQUEOS (NO OPERAR)
# =========================
def es_indecision(v):
    return cuerpo(v) < (v["max"] - v["min"]) * 0.3


def es_agotamiento(v):
    return mecha_superior(v) > cuerpo(v) * 2 or mecha_inferior(v) > cuerpo(v) * 2


def zona_resistencia_soporte(velas):
    highs = [v["max"] for v in velas[-10:]]
    lows = [v["min"] for v in velas[-10:]]

    ultimo = velas[-1]

    if abs(ultimo["close"] - max(highs)) < 0.0002:
        return True

    if abs(ultimo["close"] - min(lows)) < 0.0002:
        return True

    return False


def zona_institucional(velas):
    rango = max(v["max"] for v in velas[-8:]) - min(v["min"] for v in velas[-8:])
    return rango < 0.0004  # mercado comprimido


# =========================
# FUNCIÓN PRINCIPAL
# =========================
def detectar_entrada_oculta(data):

    if "EURUSD-OTC" not in data:
        return None

    velas = data["EURUSD-OTC"]

    if not velas or len(velas) < 10:
        return None

    direccion = tendencia_fuerte(velas)

    if not direccion:
        return None

    if not continuidad(velas, direccion):
        return None

    ultima = velas[-1]

    # 🔥 BLOQUEOS
    if es_indecision(ultima):
        return None

    if es_agotamiento(ultima):
        return None

    if zona_resistencia_soporte(velas):
        return None

    if zona_institucional(velas):
        return None

    # 🔥 SCORE SIMPLE
    score = 10

    return ("EURUSD-OTC", direccion, score)
