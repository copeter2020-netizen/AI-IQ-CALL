import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 FILTRO MERCADO ACTIVO
# ==========================
def mercado_activo(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        if vol_actual < vol_pasada * 0.8:
            return False

        return True

    except:
        return False


# ==========================
# 🔥 ESTRATEGIA CONTINUIDAD
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 CONTROL (más flexible)
    if ahora - ultima_operacion < 300:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

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
        v4 = velas[-4]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,_,_   = d(v2)
        o3,c3,_,_   = d(v3)
        o4,c4,_,_   = d(v4)

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        score = 0

        # ==========================
        # 🔥 1. TENDENCIA CLARA
        # ==========================
        p = np.polyfit(range(10), closes[-10:], 1)[0]

        if p > 0:
            direccion = "call"
            score += 25
        elif p < 0:
            direccion = "put"
            score += 25
        else:
            continue

        # ==========================
        # 🔥 2. CONTINUIDAD REAL (CLAVE)
        # ==========================
        if direccion == "call":
            if not (c1 > c2 > c3 > c4):
                continue
        else:
            if not (c1 < c2 < c3 < c4):
                continue

        score += 30

        # ==========================
        # 🔥 3. VELA ACTUAL FUERTE
        # ==========================
        if cuerpo < rango * 0.6:
            continue

        score += 15

        # ==========================
        # 🔥 4. SIN RECHAZO
        # ==========================
        if direccion == "call" and mecha_sup > cuerpo * 0.3:
            continue
        if direccion == "put" and mecha_inf > cuerpo * 0.3:
            continue

        score += 15

        # ==========================
        # 🔥 5. ACELERACIÓN
        # ==========================
        p_corto = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call" and p_corto <= p:
            continue
        if direccion == "put" and p_corto >= p:
            continue

        score += 15

        # ==========================
        # 🔥 SELECCIÓN
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 80:
        ultima_operacion = ahora
        return mejor

    return None
