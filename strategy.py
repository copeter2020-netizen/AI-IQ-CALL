import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 MERCADO OPERABLE
# ==========================
def mercado_operable(velas):
    try:
        highs = np.array([v["max"] for v in velas])
        lows  = np.array([v["min"] for v in velas])
        closes = np.array([v["close"] for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])
        rango = max(highs[-20:]) - min(lows[-20:])
        pendiente = abs(np.polyfit(range(20), closes[-20:], 1)[0])
        ruido = np.std(closes[-10:])

        if vol_actual < vol_pasada * 0.9:
            return False

        if rango < vol_actual * 2:
            return False

        if pendiente < 0.00001:
            return False

        if ruido > vol_actual:
            return False

        return True

    except:
        return False


# ==========================
# 🔥 ZONA PROHIBIDA
# ==========================
def zona_prohibida(highs, lows, precio):
    maximo = max(highs[-30:])
    minimo = min(lows[-30:])
    rango = maximo - minimo

    if rango == 0:
        return True

    pos = (precio - minimo) / rango

    # ❌ evitar extremos
    if pos > 0.85 or pos < 0.15:
        return True

    return False


# ==========================
# 🔥 SCORE PAR (SELECCIÓN)
# ==========================
def score_par(velas):
    try:
        highs = np.array([v["max"] for v in velas])
        lows  = np.array([v["min"] for v in velas])
        closes = np.array([v["close"] for v in velas])

        volatilidad = np.mean(highs[-10:] - lows[-10:])
        tendencia = abs(np.polyfit(range(10), closes[-10:], 1)[0])
        ruido = np.std(closes[-10:])

        return (volatilidad * 2) + (tendencia * 5) - ruido

    except:
        return 0


# ==========================
# 🔥 ESTRATEGIA PRINCIPAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 control de frecuencia
    if ahora - ultima_operacion < 900:
        return None

    candidatos = []

    # ==========================
    # 🔥 FILTRAR PARES
    # ==========================
    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 80:
            continue

        if not mercado_operable(velas):
            continue

        calidad = score_par(velas)
        candidatos.append((par, velas, calidad))

    # 🔥 mercado malo → no operar
    if not candidatos:
        print("💤 Mercado no óptimo...")
        return None

    # ==========================
    # 🔥 ELEGIR MEJOR PAR
    # ==========================
    candidatos.sort(key=lambda x: x[2], reverse=True)

    par, velas, _ = candidatos[0]

    highs = [v["max"] for v in velas]
    lows  = [v["min"] for v in velas]

    v1 = velas[-1]  # confirmación
    v2 = velas[-2]  # trampa

    o1, c1, h1, l1 = v1["open"], v1["close"], v1["max"], v1["min"]
    o2, c2, h2, l2 = v2["open"], v2["close"], v2["max"], v2["min"]

    # ==========================
    # ❌ ZONA PROHIBIDA
    # ==========================
    if zona_prohibida(highs, lows, c1):
        return None

    # ==========================
    # 🔥 DETECTAR TRAMPA
    # ==========================
    max_prev = max(highs[-20:-2])
    min_prev = min(lows[-20:-2])

    fake_up = h2 > max_prev and c2 < max_prev
    fake_down = l2 < min_prev and c2 > min_prev

    if fake_up:
        direccion = "put"
    elif fake_down:
        direccion = "call"
    else:
        return None

    # ==========================
    # 🔥 CONFIRMACIÓN REAL
    # ==========================
    if direccion == "put" and c1 >= c2:
        return None

    if direccion == "call" and c1 <= c2:
        return None

    # ==========================
    # 🔥 CONTINUIDAD
    # ==========================
    if direccion == "put" and c1 > o1:
        return None

    if direccion == "call" and c1 < o1:
        return None

    # ==========================
    # 🔥 VALIDACIÓN FINAL
    # ==========================
    ultima_operacion = ahora

    return (par, direccion, 100)
