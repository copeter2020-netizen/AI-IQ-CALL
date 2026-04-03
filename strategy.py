import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 INDICADORES
# ==========================
def calcular_rsi(closes, period=14):
    delta = np.diff(closes)
    gain = np.maximum(delta, 0)
    loss = np.abs(np.minimum(delta, 0))

    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calcular_ema(closes, period=20):
    return np.mean(closes[-period:])


def calcular_adx(highs, lows, closes, period=14):
    tr = highs - lows
    return np.mean(tr[-period:])


# ==========================
# 🔥 MERCADO ACTIVO
# ==========================
def mercado_activo(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        if vol_actual < vol_pasada * 0.85:
            return False

        return True

    except:
        return False


# ==========================
# 🔥 ESTRATEGIA FINAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 CONTROL
    if ahora - ultima_operacion < 180:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 50:
            continue

        if not mercado_activo(velas):
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        o1 = float(v1["open"])
        c1 = float(v1["close"])
        h1 = float(v1["max"])
        l1 = float(v1["min"])

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        # ==========================
        # 🔥 INDICADORES
        # ==========================
        rsi = calcular_rsi(closes)
        ema = calcular_ema(closes)
        adx = calcular_adx(highs, lows, closes)

        score = 0

        # ==========================
        # 🔥 1. TENDENCIA EMA
        # ==========================
        if c1 > ema:
            direccion = "call"
            score += 20
        elif c1 < ema:
            direccion = "put"
            score += 20
        else:
            continue

        # ==========================
        # 🔥 2. RSI INTELIGENTE
        # ==========================
        if direccion == "call" and rsi > 75:
            continue
        if direccion == "put" and rsi < 25:
            continue

        score += 15

        # ==========================
        # 🔥 3. CONTINUIDAD
        # ==========================
        if direccion == "call" and not (c1 > float(v2["close"]) > float(v3["close"])):
            continue
        if direccion == "put" and not (c1 < float(v2["close"]) < float(v3["close"])):
            continue

        score += 20

        # ==========================
        # 🔥 4. VELA FUERTE
        # ==========================
        if cuerpo < rango * 0.6:
            continue

        score += 10

        # ==========================
        # 🔥 5. SIN RECHAZO
        # ==========================
        if direccion == "call" and mecha_sup > cuerpo * 0.4:
            continue
        if direccion == "put" and mecha_inf > cuerpo * 0.4:
            continue

        score += 10

        # ==========================
        # 🔥 6. ADX (FUERZA)
        # ==========================
        if adx < np.mean(highs[-20:] - lows[-20:]):
            continue

        score += 15

        # ==========================
        # 🔥 SELECCIÓN
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 75:
        ultima_operacion = ahora
        return mejor

    return None
