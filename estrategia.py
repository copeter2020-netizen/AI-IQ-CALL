# estrategia.py

def detectar_entrada_oculta(data):
    """
    data = {
        "EURUSD-OTC": [
            {"open": x, "close": x, "max": x, "min": x},
            ...
        ],
        ...
    }
    """

    for par, velas in data.items():

        # Validación mínima
        if not velas or len(velas) < 20:
            continue

        try:
            closes = [v["close"] for v in velas]
            opens = [v["open"] for v in velas]
            highs = [v["max"] for v in velas]
            lows = [v["min"] for v in velas]
        except KeyError:
            continue  # evita errores si viene data incompleta

        # =========================
        # 🔥 TENDENCIA PREVIA (velas cerradas)
        # =========================
        tendencia_bajista = closes[-11] > closes[-6] > closes[-2]
        tendencia_alcista = closes[-11] < closes[-6] < closes[-2]

        # =========================
        # 🔥 IMPULSO ACTUAL (velas cerradas)
        # =========================
        ultima = velas[-2]      # última vela cerrada
        anterior = velas[-3]
        anterior2 = velas[-4]

        cuerpo1 = abs(ultima["close"] - ultima["open"])
        cuerpo2 = abs(anterior["close"] - anterior["open"])
        cuerpo3 = abs(anterior2["close"] - anterior2["open"])

        # =========================
        # 🔥 FILTROS
        # =========================
        # sin pullback
        sin_pullback = (
            lows[-2] >= lows[-3] and
            lows[-3] >= lows[-4]
        )

        sin_pullback_venta = (
            highs[-2] <= highs[-3] and
            highs[-3] <= highs[-4]
        )

        # sin agotamiento
        sin_agotamiento = cuerpo1 >= (cuerpo2 * 0.7)

        # ruptura
        ruptura_alcista = closes[-2] > highs[-6]
        ruptura_bajista = closes[-2] < lows[-6]

        # =========================
        # 📈 COMPRA
        # =========================
        if tendencia_bajista:
            if (
                ruptura_alcista and
                sin_pullback and
                sin_agotamiento and
                ultima["close"] > ultima["open"] and
                anterior["close"] > anterior["open"]
            ):
                return par, "call", 10

        # =========================
        # 📉 VENTA
        # =========================
        if tendencia_alcista:
            if (
                ruptura_bajista and
                sin_pullback_venta and
                sin_agotamiento and
                ultima["close"] < ultima["open"] and
                anterior["close"] < anterior["open"]
            ):
                return par, "put", 10

    return None
