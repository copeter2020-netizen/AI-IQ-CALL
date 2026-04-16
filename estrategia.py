def detectar_entrada_oculta(data):

    mejor_par = None
    mejor_direccion = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 20:
            continue

        cierre = [v["close"] for v in velas]

        # =========================
        # TENDENCIA
        # =========================
        ema_rapida = sum(cierre[-5:]) / 5
        ema_lenta = sum(cierre[-15:]) / 15

        tendencia_alcista = ema_rapida > ema_lenta
        tendencia_bajista = ema_rapida < ema_lenta

        # =========================
        # VELA ACTUAL
        # =========================
        ultima = velas[-1]
        anterior = velas[-2]

        cuerpo = abs(ultima["close"] - ultima["open"])
        rango = ultima["max"] - ultima["min"]

        if rango == 0:
            continue

        fuerza = cuerpo / rango

        # =========================
        # FILTRO VELA FUERTE
        # =========================
        if fuerza < 0.6:
            continue

        # =========================
        # SOPORTE / RESISTENCIA
        # =========================
        maximo = max(v["max"] for v in velas[-10:])
        minimo = min(v["min"] for v in velas[-10:])

        cerca_resistencia = ultima["close"] >= maximo * 0.998
        cerca_soporte = ultima["close"] <= minimo * 1.002

        # =========================
        # REPETICIÓN PATRÓN
        # =========================
        repeticiones = 0

        for i in range(-6, -1):
            v = velas[i]
            c = abs(v["close"] - v["open"])
            r = v["max"] - v["min"]

            if r == 0:
                continue

            if c / r > 0.5:
                repeticiones += 1

        if repeticiones < 2:
            continue

        # =========================
        # DECISIÓN FINAL
        # =========================
        score = 0

        if tendencia_alcista and ultima["close"] > ultima["open"]:

            if cerca_resistencia:
                continue  # ❌ NO COMPRAR ARRIBA

            direccion = "call"
            score = 10 + repeticiones

        elif tendencia_bajista and ultima["close"] < ultima["open"]:

            if cerca_soporte:
                continue  # ❌ NO VENDER ABAJO

            direccion = "put"
            score = 10 + repeticiones

        else:
            continue

        if score > mejor_score:
            mejor_par = par
            mejor_direccion = direccion
            mejor_score = score

    if mejor_par:
        return mejor_par, mejor_direccion, mejor_score

    return None
