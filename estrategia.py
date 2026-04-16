def detectar_entrada_oculta(data):

    mejor_par = None
    mejor_direccion = None
    mejor_score = 0

    for par, velas in data.items():

        # =========================
        # VALIDACIÓN
        # =========================
        if not velas or len(velas) < 20:
            continue

        try:
            cierres = [v["close"] for v in velas]

            # =========================
            # TENDENCIA (SMA)
            # =========================
            sma_rapida = sum(cierres[-5:]) / 5
            sma_lenta = sum(cierres[-15:]) / 15

            if sma_rapida > sma_lenta:
                tendencia = "call"
            elif sma_rapida < sma_lenta:
                tendencia = "put"
            else:
                continue

            # =========================
            # VELA ACTUAL
            # =========================
            vela = velas[-1]

            open_ = vela["open"]
            close_ = vela["close"]
            high_ = vela["max"]
            low_ = vela["min"]

            cuerpo = abs(close_ - open_)
            rango = high_ - low_

            if rango <= 0:
                continue

            fuerza = cuerpo / rango

            # ✔ Solo velas fuertes
            if fuerza < 0.6:
                continue

            # =========================
            # FILTRO DE AGOTAMIENTO
            # =========================
            ultimos = cierres[-5:]

            if tendencia == "call":
                # evita comprar en techo
                if close_ >= max(ultimos):
                    continue
            else:
                # evita vender en suelo
                if close_ <= min(ultimos):
                    continue

            # =========================
            # CONFIRMACIÓN DE PATRÓN
            # =========================
            confirmaciones = 0

            for i in range(-6, -1):
                v = velas[i]

                o = v["open"]
                c = v["close"]
                h = v["max"]
                l = v["min"]

                rango_i = h - l
                if rango_i <= 0:
                    continue

                cuerpo_i = abs(c - o)
                fuerza_i = cuerpo_i / rango_i

                if fuerza_i > 0.5:
                    if tendencia == "call" and c > o:
                        confirmaciones += 1
                    elif tendencia == "put" and c < o:
                        confirmaciones += 1

            # ✔ mínimo repetición
            if confirmaciones < 2:
                continue

            # =========================
            # SCORE FINAL
            # =========================
            score = (fuerza * 10) + confirmaciones

            if score > mejor_score:
                mejor_score = score
                mejor_par = par
                mejor_direccion = tendencia

        except Exception:
            # evita que un par rompa todo el bot
            continue

    if mejor_par:
        return mejor_par, mejor_direccion, round(mejor_score, 2)

    return None
