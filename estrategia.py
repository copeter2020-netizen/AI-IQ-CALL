# estrategia.py

# =========================
# COMPATIBILIDAD BOT
# =========================
def calculate_indicators(candles):
    # No usamos indicadores, pero mantenemos la función
    return candles


# =========================
# UTILIDADES
# =========================
def es_doji(c):
    cuerpo = abs(c['close'] - c['open'])
    rango = c['max'] - c['min']
    return cuerpo <= (rango * 0.2)


def es_fuerte(c):
    cuerpo = abs(c['close'] - c['open'])
    rango = c['max'] - c['min']
    return cuerpo >= (rango * 0.6)


def direccion(c):
    return "call" if c['close'] > c['open'] else "put"


# =========================
# LOGICA SNIPER CONTINUIDAD
# =========================
def detectar_continuidad(candles):
    c1 = candles[-3]
    c2 = candles[-2]
    c3 = candles[-1]

    # ❌ evitar basura
    if es_doji(c3):
        return None, 0

    if not es_fuerte(c3):
        return None, 0

    d1 = direccion(c1)
    d2 = direccion(c2)
    d3 = direccion(c3)

    # 🔥 tendencia fuerte
    if d1 == d2 == d3:
        return d3, 1.0

    # ✔ continuación válida
    if d2 == d3:
        return d3, 0.8

    return None, 0


# =========================
# SEÑAL PRINCIPAL
# =========================
def check_signal(candles):
    if len(candles) < 3:
        return None

    signal, fuerza = detectar_continuidad(candles)

    if signal and fuerza >= 0.8:
        return signal

    return None


# =========================
# SCORE DE CALIDAD
# =========================
def score_pair(candles):
    if len(candles) < 5:
        return 0

    ultimas = candles[-5:]
    score = 0

    # limpiar ruido
    for c in ultimas:
        if not es_doji(c):
            score += 1

    # tendencia dominante
    calls = sum(1 for c in ultimas if direccion(c) == "call")
    puts = sum(1 for c in ultimas if direccion(c) == "put")

    if calls >= 4 or puts >= 4:
        score += 2

    return score
