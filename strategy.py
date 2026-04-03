import time
import numpy as np

ultima_operacion = 0


def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO (3–6 horas)
    if ahora - ultima_operacion < 10800:
        return None

    # ⏱️ SOLO AL CIERRE DE VELA (segundo 59–60)
    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if len(velas) < 120:
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]  # vela actual (clave)
        v2 = velas[-2]
        v3 = velas[-3]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,h2,l2 = d(v2)
        o3,c3,h3,l3 = d(v3)

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        # 🔥 POSICIÓN DEL CIERRE (CLAVE ABSOLUTA)
        posicion = (c1 - l1) / rango  # 0 a 1

        score = 0

        # ==========================
        # 🔥 1. ESTRUCTURA
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
        # 🔥 2. PRESIÓN INMEDIATA
        # ==========================
        if direccion == "call" and not (c1 > c2 > c3):
            continue
        if direccion == "put" and not (c1 < c2 < c3):
            continue

        score += 15

        # ==========================
        # 🔥 3. LECTURA FINAL DE LA VELA (CLAVE)
        # ==========================
        if direccion == "call":
            if posicion < 0.85:
                continue
            if mecha_sup > cuerpo * 0.3:
                continue
        else:
            if posicion > 0.15:
                continue
            if mecha_inf > cuerpo * 0.3:
                continue

        score += 25

        # ==========================
        # 🔥 4. CUERPO DOMINANTE
        # ==========================
        if cuerpo < rango * 0.7:
            continue

        score += 10

        # ==========================
        # 🔥 5. MOMENTUM
        # ==========================
        p1 = np.polyfit(range(20), closes[-20:], 1)[0]
        p2 = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call" and not (p2 > p1 > 0):
            continue
        if direccion == "put" and not (p2 < p1 < 0):
            continue

        score += 10

        # ==========================
        # 🔥 6. RUPTURA REAL
        # ==========================
        if direccion == "call" and c1 <= h2:
            continue
        if direccion == "put" and c1 >= l2:
            continue

        score += 10

        # ==========================
        # 🔥 7. VOLATILIDAD
        # ==========================
        vol_now = np.mean(highs[-10:] - lows[-10:])
        vol_old = np.mean(highs[-40:] - lows[-40:])

        if vol_now <= vol_old:
            continue

        score += 10

        # ==========================
        # 🔥 MEJOR PAR
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    # 🔥 SOLO ENTRADAS PERFECTAS
    if mejor and mejor_score >= 95:
        ultima_operacion = ahora
        return mejor

    return None
