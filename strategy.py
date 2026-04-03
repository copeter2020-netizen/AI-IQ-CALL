import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 MERCADO VÁLIDO
# ==========================
def mercado_valido(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        rango = max(highs[-20:]) - min(lows[-20:])

        if vol_actual < vol_pasada * 0.9:
            return False

        if rango < vol_actual * 2:
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

    posicion = (precio - minimo) / rango

    if posicion > 0.85:
        return True

    if posicion < 0.15:
        return True

    return False


# ==========================
# 🔥 SCORE PAR
# ==========================
def score_par(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])
        closes = np.array([float(v["close"]) for v in velas])

        volatilidad = np.mean(highs[-10:] - lows[-10:])
        tendencia = abs(np.polyfit(range(10), closes[-10:], 1)[0])
        ruido = np.std(closes[-10:])

        return (volatilidad * 2) + (tendencia * 5) - ruido
    except:
        return 0


# ==========================
# 🔥 ESTRATEGIA FINAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 900:
        return None

    candidatos = []

    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 80:
            continue

        if not mercado_valido(velas):
            continue

        calidad = score_par(velas)

        candidatos.append((par, velas, calidad))

    if not candidatos:
        return None

    candidatos.sort(key=lambda x: x[2], reverse=True)

    par, velas, _ = candidatos[0]

    closes = np.array([float(v["close"]) for v in velas])
    highs  = np.array([float(v["max"]) for v in velas])
    lows   = np.array([float(v["min"]) for v in velas])

    v1 = velas[-1]
    v2 = velas[-2]

    o1 = float(v1["open"])
    c1 = float(v1["close"])
    h1 = float(v1["max"])
    l1 = float(v1["min"])

    o2 = float(v2["open"])
    c2 = float(v2["close"])
    h2 = float(v2["max"])
    l2 = float(v2["min"])

    # ==========================
    # ❌ NO OPERAR EN ZONA
    # ==========================
    if zona_prohibida(highs, lows, c1):
        return None

    # ==========================
    # 🔥 TRAMPA
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
    # 🔥 CONFIRMACIÓN
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
    # 🔥 ESPERAR SIGUIENTE VELA
    # ==========================
    segundos = int(time.time()) % 60
    esperar = 60 - segundos

    if esperar > 0:
        time.sleep(esperar)

    ultima_operacion = time.time()

    return (par, direccion, 100)
