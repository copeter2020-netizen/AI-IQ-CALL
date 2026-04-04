import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 RSI
# ==========================
def rsi(closes, period=14):
    delta = np.diff(closes)
    gain = np.maximum(delta, 0)
    loss = np.abs(np.minimum(delta, 0))

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ==========================
# 🔥 CCI
# ==========================
def cci(highs, lows, closes, period=20):
    tp = (highs + lows + closes) / 3
    sma = np.mean(tp[-period:])
    mad = np.mean(np.abs(tp[-period:] - sma))

    if mad == 0:
        return 0

    return (tp[-1] - sma) / (0.015 * mad)


# ==========================
# 🔥 ATR
# ==========================
def atr(highs, lows, period=14):
    return np.mean(highs[-period:] - lows[-period:])


# ==========================
# 🔥 MERCADO ACTIVO
# ==========================
def mercado_valido(highs, lows):
    vol_actual = np.mean(highs[-5:] - lows[-5:])
    vol_pasada = np.mean(highs[-30:] - lows[-30:])
    return vol_actual > vol_pasada * 0.9


# ==========================
# 🔥 SCORE PAR
# ==========================
def score_par(highs, lows, closes):
    volatilidad = np.mean(highs[-10:] - lows[-10:])
    tendencia = abs(np.polyfit(range(10), closes[-10:], 1)[0])
    ruido = np.std(closes[-10:])
    return (volatilidad * 2) + (tendencia * 5) - ruido


# ==========================
# 🔥 VALIDAR CONTINUIDAD
# ==========================
def vela_continuidad(o, c, h, l, direccion):

    rango = h - l
    if rango == 0:
        return False

    cuerpo = abs(c - o)
    posicion = (c - l) / rango

    mecha_sup = h - max(o, c)
    mecha_inf = min(o, c) - l

    # 🔥 CUERPO FUERTE
    if cuerpo < rango * 0.7:
        return False

    # 🔥 SIN RECHAZO
    if mecha_sup > cuerpo * 0.3 or mecha_inf > cuerpo * 0.3:
        return False

    # 🔥 POSICIÓN DE CIERRE
    if direccion == "call" and posicion < 0.85:
        return False

    if direccion == "put" and posicion > 0.15:
        return False

    return True


# ==========================
# 🔥 ESTRATEGIA FINAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 600:
        return None

    candidatos = []

    for par, velas in data_por_par.items():

        if len(velas) < 60:
            continue

        closes = np.array([v["close"] for v in velas])
        highs  = np.array([v["max"] for v in velas])
        lows   = np.array([v["min"] for v in velas])

        if not mercado_valido(highs, lows):
            continue

        calidad = score_par(highs, lows, closes)
        candidatos.append((par, velas, calidad))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[2], reverse=True)
    par, velas, _ = candidatos[0]

    closes = np.array([v["close"] for v in velas])
    highs  = np.array([v["max"] for v in velas])
    lows   = np.array([v["min"] for v in velas])

    r = rsi(closes)
    c = cci(highs, lows, closes)
    a = atr(highs, lows)

    pendiente = np.polyfit(range(10), closes[-10:], 1)[0]
    pendiente_corta = np.polyfit(range(5), closes[-5:], 1)[0]

    v1 = velas[-1]
    v2 = velas[-2]

    o1, c1, h1, l1 = v1["open"], v1["close"], v1["max"], v1["min"]
    o2, c2, h2, l2 = v2["open"], v2["close"], v2["max"], v2["min"]

    score = 0

    # ==========================
    # 🔥 EXTREMO
    # ==========================
    if r > 75 and c > 100:
        direccion = "put"
        score += 20
    elif r < 25 and c < -100:
        direccion = "call"
        score += 20
    else:
        return None

    # ==========================
    # 🔥 VOLATILIDAD
    # ==========================
    if a < np.mean(highs[-30:] - lows[-30:]):
        return None

    score += 10

    # ==========================
    # 🔥 TRAMPA (LIQUIDEZ)
    # ==========================
    max_prev = max(highs[-20:-2])
    min_prev = min(lows[-20:-2])

    fake_up = h2 > max_prev and c2 < max_prev
    fake_down = l2 < min_prev and c2 > min_prev

    if direccion == "put" and not fake_up:
        return None

    if direccion == "call" and not fake_down:
        return None

    score += 20

    # ==========================
    # 🔥 PÉRDIDA DE FUERZA
    # ==========================
    if direccion == "put" and pendiente_corta < pendiente:
        score += 15
    elif direccion == "call" and pendiente_corta > pendiente:
        score += 15
    else:
        return None

    # ==========================
    # 🔥 CONTINUIDAD REAL (CLAVE FINAL)
    # ==========================
    if not vela_continuidad(o1, c1, h1, l1, direccion):
        return None

    score += 35

    # ==========================
    # 🔥 SOLO PERFECTAS
    # ==========================
    if score >= 90:
        ultima_operacion = ahora
        return (par, direccion, score)

    return None
