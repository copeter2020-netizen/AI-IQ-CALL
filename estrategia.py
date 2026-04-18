def detectar_entrada_oculta(data):
    for par, velas in data.items():

        if len(velas) < 20:
            continue

        closes = [v["close"] for v in velas]
        opens = [v["open"] for v in velas]
        highs = [v["max"] for v in velas]
        lows = [v["min"] for v in velas]

        # =========================
        # 🔥 TENDENCIA PREVIA
        # =========================
        tendencia_bajista = closes[-10] > closes[-5] > closes[-1]
        tendencia_alcista = closes[-10] < closes[-5] < closes[-1]

        # =========================
        # 🔥 IMPULSO ACTUAL
        # =========================
        ultima = velas[-1]
        anterior = velas[-2]
        anterior2 = velas[-3]

        cuerpo1 = abs(ultima["close"] - ultima["open"])
        cuerpo2 = abs(anterior["close"] - anterior["open"])
        cuerpo3 = abs(anterior2["close"] - anterior2["open"])

        # =========================
        # 🔥 FILTROS
        # =========================
        # sin pullback (velas limpias)
        sin_pullback = (
            lows[-1] >= lows[-2] and
            lows[-2] >= lows[-3]
        )

        sin_pullback_venta = (
            highs[-1] <= highs[-2] and
            highs[-2] <= highs[-3]
        )

        # sin agotamiento (cuerpos consistentes)
        sin_agotamiento = cuerpo1 >= cuerpo2 * 0.7

        # ruptura (máximo o mínimo anterior)
        ruptura_alcista = ultima["close"] > highs[-5]
        ruptura_bajista = ultima["close"] < lows[-5]

        # =========================
        # 📈 COMPRA (ruptura de bajista)
        # =========================
        if tendencia_bajista:

            if (
                ruptura_alcista and
                sin_pullback and
                sin_agotamiento and
                ultima["close"] > ultima["open"] and
                anterior["close"] > anterior["open"]
            ):
                score = 10
                return par, "call", score

        # =========================
        # 📉 VENTA (ruptura de alcista)
        # =========================
        if tendencia_alcista:

            if (
                ruptura_bajista and
                sin_pullback_venta and
                sin_agotamiento and
                ultima["close"] < ultima["open"] and
                anterior["close"] < anterior["open"]
            ):
                score = 10
                return par, "put", score

    return None
