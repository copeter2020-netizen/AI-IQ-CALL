import numpy as np

# ========================
# DATOS
# ========================

def get_close(velas):
    return [float(v["close"]) for v in velas]

def get_open(velas):
    return [float(v["open"]) for v in velas]

def get_high(velas):
    return [float(v["max"]) for v in velas]

def get_low(velas):
    return [float(v["min"]) for v in velas]

# ========================
# GRÁFICO DE LÍNEA (TENDENCIA)
# ========================

def tendencia_linea(velas):
    closes = get_close(velas)

    if len(closes) < 10:
        return None

    # regresión simple
    x = np.arange(len(closes))
    y = np.array(closes)

    pendiente = np.polyfit(x, y, 1)[0]

    if pendiente > 0:
        return "alcista"
    elif pendiente < 0:
        return "bajista"
    else:
        return None

# ========================
# SOPORTE / RESISTENCIA
# ========================

def zonas(velas):
    highs = get_high(velas[-30:])
    lows = get_low(velas[-30:])

    return min(lows), max(highs)

# ========================
# FUERZA DE VELA
# ========================

def fuerza_vela(vela):
    body = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return 0

    return body / rango

# ========================
# DETECCIÓN FINAL
# ========================

def detectar_entrada(velas):
    try:
        if isinstance(velas, tuple):
            velas = velas[1]

        if len(velas) < 20:
            return None

        ultima = velas[-1]
        anterior = velas[-2]

        soporte, resistencia = zonas(velas)

        tendencia = tendencia_linea(velas)

        fuerza = fuerza_vela(ultima)

        cierre = float(ultima["close"])
        apertura = float(ultima["open"])

        # ========================
        # FILTRO: EVITAR RANGO
        # ========================
        rango = resistencia - soporte

        if rango < 0.0003:
            return None

        # ========================
        # SOPORTE (REBOTE)
        # ========================
        if cierre <= soporte + 0.0002:
            if cierre > apertura and fuerza > 0.5:
                return "call"

        # ========================
        # RESISTENCIA (REBOTE)
        # ========================
        if cierre >= resistencia - 0.0002:
            if cierre < apertura and fuerza > 0.5:
                return "put"

        # ========================
        # CONTINUIDAD + TENDENCIA
        # ========================
        if tendencia == "alcista":
            if cierre > apertura and fuerza > 0.6:
                return "call"

        if tendencia == "bajista":
            if cierre < apertura and fuerza > 0.6:
                return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
