def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO (3–6h)
    if ahora - ultima_operacion < 10800:
        return None

    # ⏱️ SOLO AL FINAL DE VELA
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

        v1 = velas[-1]
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

        score = 0

        # ==========================
        # 🔥 1. ESTRUCTURA REAL
        # ==========================
        hh = highs[-1] > highs[-5] > highs[-10]
        hl = lows[-1] > lows[-5] > lows[-10]

        ll = highs[-1] < highs[-5] < highs[-10]
        lh = lows[-1] < lows[-5] < lows[-10]

        if hh and hl:
            direccion = "call"
            score += 25
        elif ll and lh:
            direccion = "put"
            score += 25
        else:
            continue

        # ==========================
        # 🔥 2. PRESIÓN INMEDIATA (CLAVE)
        # ==========================
        if direccion == "call":
            if not (c1 > c2 > c3):
                continue
        else:
            if not (c1 < c2 < c3):
                continue

        score += 20

        # ==========================
        # 🔥 3. CIERRE DOMINANTE
        # ==========================
        if direccion == "call":
            if c1 < h1 - rango * 0.15:
                continue
        else:
            if c1 > l1 + rango * 0.15:
                continue

        score += 15

        # ==========================
        # 🔥 4. SIN RECHAZO (MUY CLAVE)
        # ==========================
        if mecha_sup > cuerpo * 0.6 or mecha_inf > cuerpo * 0.6:
            continue

        score += 15

        # ==========================
        # 🔥 5. MOMENTUM (ACELERACIÓN)
        # ==========================
        p1 = np.polyfit(range(20), closes[-20:], 1)[0]
        p2 = np.polyfit(range(5), closes[-5:], 1)[0]

        if direccion == "call":
            if not (p2 > p1 > 0):
                continue
        else:
            if not (p2 < p1 < 0):
                continue

        score += 15

        # ==========================
        # 🔥 6. VOLATILIDAD (MEJOR PAR)
        # ==========================
        vol_now = np.mean(highs[-10:] - lows[-10:])
        vol_old = np.mean(highs[-40:] - lows[-40:])

        if vol_now <= vol_old:
            continue

        score += 10

        # ==========================
        # 🔥 7. RUPTURA REAL
        # ==========================
        if direccion == "call" and c1 <= h2:
            continue
        if direccion == "put" and c1 >= l2:
            continue

        score += 10

        # ==========================
        # 🔥 SELECCIÓN FINAL
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    # 🔥 SOLO ENTRADAS PERFECTAS REALES
    if mejor and mejor_score >= 95:
        ultima_operacion = ahora
        return mejor

    return None
