# estrategia.py

def calcular_rsi(closes, periodo=14):
    if len(closes) < periodo + 1:
        return None

    ganancias, perdidas = [], []

    for i in range(-periodo, 0):
        cambio = closes[i] - closes[i - 1]
        if cambio > 0:
            ganancias.append(cambio)
            perdidas.append(0)
        else:
            ganancias.append(0)
            perdidas.append(abs(cambio))

    avg_g = sum(ganancias) / periodo
    avg_p = sum(perdidas) / periodo

    if avg_p == 0:
        return 100

    rs = avg_g / avg_p
    return 100 - (100 / (1 + rs))


def detectar_entrada_oculta(data):
    for par, velas in data.items():

        # 🔥 SOLO EURUSD
        if par != "EURUSD-OTC":
            continue

        if not velas or len(velas) < 20:
            continue

        closes = [v["close"] for v in velas]
        highs = [v["max"] for v in velas]
        lows = [v["min"] for v in velas]

        # =========================
        # VELAS CERRADAS
        # =========================
        ultima = velas[-2]
        anterior = velas[-3]
        anterior2 = velas[-4]

        cuerpo1 = abs(ultima["close"] - ultima["open"])
        cuerpo2 = abs(anterior["close"] - anterior["open"])
        cuerpo3 = abs(anterior2["close"] - anterior2["open"])

        # =========================
        # TENDENCIA
        # =========================
        tendencia_bajista = closes[-11] > closes[-6] > closes[-2]
        tendencia_alcista = closes[-11] < closes[-6] < closes[-2]

        # =========================
        # FILTROS
        # =========================
        sin_pullback = lows[-2] >= lows[-3] >= lows[-4]
        sin_pullback_venta = highs[-2] <= highs[-3] <= highs[-4]
        sin_agotamiento = cuerpo1 >= cuerpo2 * 0.7

        ruptura_alcista = closes[-2] > highs[-6]
        ruptura_bajista = closes[-2] < lows[-6]

        # =========================
        # ESTRATEGIA 1
        # =========================
        if tendencia_bajista:
            if ruptura_alcista and sin_pullback and sin_agotamiento and ultima["close"] > ultima["open"] and anterior["close"] > anterior["open"]:
                return par, "call", 10

        if tendencia_alcista:
            if ruptura_bajista and sin_pullback_venta and sin_agotamiento and ultima["close"] < ultima["open"] and anterior["close"] < anterior["open"]:
                return par, "put", 10

        # =========================
        # ESTRATEGIA 2 (RSI)
        # =========================
        rsi = calcular_rsi(closes)

        if rsi:
            if rsi <= 30 and ultima["close"] > ultima["open"] and anterior["close"] > anterior["open"]:
                return par, "call", 9

            if rsi >= 70 and ultima["close"] < ultima["open"] and anterior["close"] < anterior["open"]:
                return par, "put", 9

        # =========================
        # ESTRATEGIA 3 (MOMENTUM)
        # =========================
        if cuerpo1 > cuerpo2 > cuerpo3:
            if ultima["close"] > ultima["open"] and anterior["close"] > anterior["open"]:
                return par, "call", 8

            if ultima["close"] < ultima["open"] and anterior["close"] < anterior["open"]:
                return par, "put", 8

        # =========================
        # ESTRATEGIA 4 (PRICE ACTION)
        # =========================
        mecha_inf = min(ultima["open"], ultima["close"]) - ultima["min"]
        mecha_sup = ultima["max"] - max(ultima["open"], ultima["close"])
        cuerpo = abs(ultima["close"] - ultima["open"])

        if mecha_inf > cuerpo * 1.5 and ultima["close"] > ultima["open"]:
            return par, "call", 7

        if mecha_sup > cuerpo * 1.5 and ultima["close"] < ultima["open"]:
            return par, "put", 7

    return None
