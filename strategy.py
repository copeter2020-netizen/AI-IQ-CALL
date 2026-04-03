import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 FILTRO NO OPERAR
# ==========================
def mercado_valido(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        rango = max(highs[-20:]) - min(lows[-20:])

        # ❌ mercado muerto
        if vol_actual < vol_pasada * 0.9:
            return False

        # ❌ rango comprimido
        if rango < vol_actual * 2:
            return False

        return True
    except:
        return False


# ==========================
# 🔥 ESTRATEGIA FINAL ABSOLUTA
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO
    if ahora - ultima_operacion < 900:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 80:
            continue

        if not mercado_valido(velas):
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]  # confirmación
        v2 = velas[-2]  # trampa
        v3 = velas[-3]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,h2,l2 = d(v2)

        rango2 = h2 - l2
        if rango2 == 0:
            continue

        cuerpo2 = abs(c2 - o2)

        score = 0

        # ==========================
        # 🔥 1. DETECTAR TRAMPA
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
            continue

        score += 30

        # ==========================
        # 🔥 2. RECHAZO REAL
        # ==========================
        if direccion == "put":
            if (h2 - max(o2, c2)) < cuerpo2 * 1.2:
                continue
        else:
            if (min(o2, c2) - l2) < cuerpo2 * 1.2:
                continue

        score += 20

        # ==========================
        # 🔥 3. CONFIRMACIÓN (CLAVE)
        # ==========================
        if direccion == "put" and c1 >= c2:
            continue
        if direccion == "call" and c1 <= c2:
            continue

        score += 25

        # ==========================
        # 🔥 4. CONTINUACIÓN
        # ==========================
        if direccion == "put" and c1 > o1:
            continue
        if direccion == "call" and c1 < o1:
            continue

        score += 15

        # ==========================
        # 🔥 5. ESPACIO LIBRE
        # ==========================
        maximo = max(highs[-30:])
        minimo = min(lows[-30:])

        if direccion == "put" and (c1 - minimo) < rango2:
            continue
        if direccion == "call" and (maximo - c1) < rango2:
            continue

        score += 10

        # ==========================
        # 🔥 SELECCIÓN FINAL
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 90:
        ultima_operacion = ahora
        return mejor

    return None
