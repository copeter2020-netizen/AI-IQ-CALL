import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 MERCADO ACTIVO
# ==========================
def mercado_activo(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        if vol_actual < vol_pasada * 0.9:
            return False

        return True
    except:
        return False


# ==========================
# 🔥 ESTRATEGIA SMART MONEY
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 600:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 80:
            continue

        if not mercado_activo(velas):
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,h2,l2 = d(v2)
        o3,c3,h3,l3 = d(v3)

        rango1 = h1 - l1
        if rango1 == 0:
            continue

        cuerpo1 = abs(c1 - o1)

        mecha_sup1 = h1 - max(o1, c1)
        mecha_inf1 = min(o1, c1) - l1

        score = 0

        # ==========================
        # 🔥 1. TENDENCIA PREVIA
        # ==========================
        pendiente = np.polyfit(range(15), closes[-15:], 1)[0]

        if pendiente > 0:
            direccion = "put"
        elif pendiente < 0:
            direccion = "call"
        else:
            continue

        score += 15

        # ==========================
        # 🔥 2. LIQUIDITY GRAB (CLAVE)
        # ==========================
        max_prev = max(highs[-20:-1])
        min_prev = min(lows[-20:-1])

        fake_break_up = h1 > max_prev and c1 < max_prev
        fake_break_down = l1 < min_prev and c1 > min_prev

        if direccion == "put" and not fake_break_up:
            continue
        if direccion == "call" and not fake_break_down:
            continue

        score += 30

        # ==========================
        # 🔥 3. RECHAZO FUERTE
        # ==========================
        if direccion == "put":
            if mecha_sup1 < cuerpo1 * 1.5:
                continue
        else:
            if mecha_inf1 < cuerpo1 * 1.5:
                continue

        score += 20

        # ==========================
        # 🔥 4. CIERRE DÉBIL (CLAVE)
        # ==========================
        if direccion == "put" and c1 > o1:
            continue
        if direccion == "call" and c1 < o1:
            continue

        score += 10

        # ==========================
        # 🔥 5. CONTEXTO EXTREMO
        # ==========================
        maximo = max(highs[-30:])
        minimo = min(lows[-30:])

        posicion = (c1 - minimo) / (maximo - minimo)

        if direccion == "put" and posicion < 0.85:
            continue
        if direccion == "call" and posicion > 0.15:
            continue

        score += 15

        # ==========================
        # 🔥 6. PÉRDIDA DE FUERZA
        # ==========================
        p_corto = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "put" and p_corto > 0:
            score += 10
        elif direccion == "call" and p_corto < 0:
            score += 10
        else:
            continue

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
