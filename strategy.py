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

        rango = max(highs[-20:]) - min(lows[-20:])

        if vol_actual < vol_pasada * 0.8:
            return False

        if rango < vol_actual * 2:
            return False

        return True

    except:
        return False


# ==========================
# 🔥 ESTRATEGIA SNIPER
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO
    if ahora - ultima_operacion < 1800:
        return None

    # ⏱️ SOLO AL FINAL
    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if len(velas) < 120:
            continue

        # 🔥 FILTRO MERCADO ACTIVO
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
        o3,c3,_,_   = d(v3)

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        posicion = (c1 - l1) / rango

        score = 0

        # ==========================
        # 🔥 ESTRUCTURA
        # ==========================
        hh = highs[-1] > highs[-5] > highs[-10]
        hl = lows[-1] > lows[-5] > lows[-10]

        ll = highs[-1] < highs[-5] < highs[-10]
        lh = lows[-1] < lows[-5] < lows[-10]

        if hh and hl:
            direccion = "call"
            score += 20
        elif ll and lh:
            direccion = "put"
            score += 20
        else:
            continue

        # ==========================
        # 🔥 COMPRESIÓN → EXPANSIÓN
        # ==========================
        vol_ant = np.mean(highs[-15:-5] - lows[-15:-5])
        vol_act = np.mean(highs[-5:] - lows[-5:])

        if vol_act <= vol_ant:
            continue

        score += 20

        # ==========================
        # 🔥 PRESIÓN
        # ==========================
        if direccion == "call" and not (c1 > c2 > c3):
            continue
        if direccion == "put" and not (c1 < c2 < c3):
            continue

        score += 20

        # ==========================
        # 🔥 VELA FINAL (CLAVE)
        # ==========================
        if direccion == "call":
            if posicion < 0.9 or mecha_sup > cuerpo * 0.25:
                continue
        else:
            if posicion > 0.1 or mecha_inf > cuerpo * 0.25:
                continue

        score += 25

        # ==========================
        # 🔥 CUERPO
        # ==========================
        if cuerpo < rango * 0.75:
            continue

        score += 10

        # ==========================
        # 🔥 MOMENTUM
        # ==========================
        p = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call" and p <= 0:
            continue
        if direccion == "put" and p >= 0:
            continue

        score += 15

        # ==========================
        # 🔥 RUPTURA
        # ==========================
        if direccion == "call" and c1 <= h2:
            continue
        if direccion == "put" and c1 >= l2:
            continue

        score += 10

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 100:
        ultima_operacion = ahora
        return mejor

    return None
