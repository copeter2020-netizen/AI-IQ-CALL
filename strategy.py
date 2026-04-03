import statistics

# ========= UTIL =========
def cuerpo(vela):
    return abs(vela["close"] - vela["open"])

def rango(vela):
    return vela["max"] - vela["min"]

def es_alcista(vela):
    return vela["close"] > vela["open"]

def es_bajista(vela):
    return vela["close"] < vela["open"]


# ========= ANALISIS VELAS =========
def analizar_vela(vela, velas):
    c = cuerpo(vela)
    r = rango(vela)

    promedio = statistics.mean([cuerpo(v) for v in velas[-10:]])

    # FUERZA
    if c > promedio * 1.5 and r > promedio * 1.5:
        return "fuerza"

    # DEBILIDAD
    if c < promedio * 0.5:
        return "debilidad"

    # AGOTAMIENTO (mecha grande)
    mecha_sup = vela["max"] - max(vela["open"], vela["close"])
    mecha_inf = min(vela["open"], vela["close"]) - vela["min"]

    if mecha_sup > c or mecha_inf > c:
        return "agotamiento"

    # CONTINUACIÓN
    return "continuacion"


# ========= ANALISIS LINEA =========
def analizar_linea(velas):
    cierres = [v["close"] for v in velas[-10:]]

    sube = sum(1 for i in range(1, len(cierres)) if cierres[i] > cierres[i-1])
    baja = sum(1 for i in range(1, len(cierres)) if cierres[i] < cierres[i-1])

    # FUERZA
    if sube >= 7:
        return "fuerza_alcista"
    if baja >= 7:
        return "fuerza_bajista"

    # DEBILIDAD
    if abs(sube - baja) <= 2:
        return "debilidad"

    # AGOTAMIENTO (pierde ritmo)
    if cierres[-1] < cierres[-2] and cierres[-2] > cierres[-3]:
        return "agotamiento_bajista"

    if cierres[-1] > cierres[-2] and cierres[-2] < cierres[-3]:
        return "agotamiento_alcista"

    return "continuacion"


# ========= DECISION FINAL =========
def detectar_entrada(velas):
    if len(velas) < 20:
        return None

    ultima = velas[-1]

    # análisis vela
    tipo_vela = analizar_vela(ultima, velas)

    # análisis línea
    tipo_linea = analizar_linea(velas)

    # ===== LOGICA =====

    # VENTA (PUT)
    if (
        tipo_linea in ["fuerza_bajista", "continuacion"] and
        tipo_vela in ["continuacion", "fuerza"]
    ):
        return "put"

    # COMPRA (CALL)
    if (
        tipo_linea in ["fuerza_alcista", "continuacion"] and
        tipo_vela in ["continuacion", "fuerza"]
    ):
        return "call"

    # REBOTES (AGOTAMIENTO)
    if tipo_vela == "agotamiento":
        if es_bajista(ultima):
            return "call"
        if es_alcista(ultima):
            return "put"

    return None
