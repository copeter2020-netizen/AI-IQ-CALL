def detectar_entrada_oculta(data):
    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        closes = [v["close"] for v in velas]
        highs = [v["max"] for v in velas]
        lows = [v["min"] for v in velas]

        # =========================
        # TENDENCIA (estructura)
        # =========================
        tendencia_alcista = closes[-1] > closes[-5] > closes[-10]
        tendencia_bajista = closes[-1] < closes[-5] < closes[-10]

        if not tendencia_alcista and not tendencia_bajista:
            continue

        # =========================
        # IMPULSO
        # =========================
        cuerpo = abs(closes[-1] - velas[-1]["open"])
        rango = highs[-1] - lows[-1]

        if rango == 0:
            continue

        fuerza = cuerpo / rango

        if fuerza < 0.6:
            continue

        # =========================
        # RETROCESO POR ESTRUCTURA
        # =========================
        retroceso = abs(closes[-2] - closes[-3]) < abs(closes[-4] - closes[-5])

        if not retroceso:
            continue

        # =========================
        # SOPORTE / RESISTENCIA SIMPLE
        # =========================
        zona_alta = max(highs[-10:])
        zona_baja = min(lows[-10:])

        cerca_resistencia = closes[-1] >= zona_alta * 0.998
        cerca_soporte = closes[-1] <= zona_baja * 1.002

        # =========================
        # DIRECCIÓN FINAL
        # =========================
        direccion = None
        score = 0

        if tendencia_alcista and not cerca_resistencia:
            direccion = "call"
            score += 5

        elif tendencia_bajista and not cerca_soporte:
            direccion = "put"
            score += 5

        else:
            continue

        # =========================
        # FILTRO DE AGOTAMIENTO
        # =========================
        if fuerza > 0.9:
            continue

        score += fuerza * 10

        # =========================
        # REPETICIÓN DE PATRÓN
        # =========================
        repeticiones = 0
        for i in range(-10, -2):
            if abs(closes[i] - closes[i-1]) > abs(closes[i-2] - closes[i-3]):
                repeticiones += 1

        if repeticiones < 3:
            continue

        score += repeticiones

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, round(score, 2))

    return mejor
