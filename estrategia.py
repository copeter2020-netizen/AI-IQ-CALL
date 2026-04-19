# estrategia.py

def calcular_rsi(closes, periodo=14):
    if len(closes) < periodo + 1:
        return None

    ganancias = []
    perdidas = []

    for i in range(-periodo, 0):
        cambio = closes[i] - closes[i - 1]
        if cambio > 0:
            ganancias.append(cambio)
            perdidas.append(0)
        else:
            ganancias.append(0)
            perdidas.append(abs(cambio))

    avg_ganancia = sum(ganancias) / periodo
    avg_perdida = sum(perdidas) / periodo

    if avg_perdida == 0:
        return 100

    rs = avg_ganancia / avg_perdida
    return 100 - (100 / (1 + rs))


def detectar_entrada_oculta(data):
    for par, velas in data.items():

        if not velas or len(velas) < 20:
            continue

        try:
            closes = [v["close"] for v in velas]
            opens = [v["open"] for v in velas]
            highs = [v["max"] for v in velas]
            lows = [v["min"] for v in velas]
        except:
            continue

        # =========================
        # 🔥 VELAS CERRADAS
        # =========================
        ultima = velas[-2]
        anterior = velas[-3]
        anterior2 = velas[-4]

        cuerpo1 = abs(ultima["close"] - ultima["open"])
        cuerpo2 = abs(anterior["close"] - anterior["open"])
        cuerpo3 = abs(anterior2["close"] - anterior2["open"])

        # =========================
        # 🔥 TENDENCIA
        # =========================
        tendencia_bajista = closes[-11] > closes[-6] > closes[-2]
        tendencia_alcista = closes[-11] < closes[-6] < closes[-2]

        # =========================
        # 🔥 FILTROS
        # =========================
        sin_pullback = lows[-2] >= lows[-3] >= lows[-4]
        sin_pullback_venta = highs[-2] <= highs[-3] <= highs[-4]

        sin_agotamiento = cuerpo1 >= (cuerpo2 * 0.7)

        ruptura_alcista = closes[-2] > highs[-6]
        ruptura_bajista = closes[-2] < lows[-6]

        # =========================
        # 📈 ESTRATEGIA 1 (CONTINUIDAD)
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

        if tendencia_alcista:
            if (
                ruptura_bajista and
                sin_pullback_venta and
                sin_agotamiento and
                ultima["close"] < ultima["open"] and
                anterior["close"] < anterior["open"]
            ):
                return par, "put", 10

        # =========================
        # 📊 ESTRATEGIA 2 (RSI)
        # =========================
        rsi = calcular_rsi(closes)

        if rsi is not None:

            if rsi <= 30:
                if ultima["close"] > ultima["open"] and anterior["close"] > anterior["open"]:
                    return par, "call", 9

            if rsi >= 70:
                if ultima["close"] < ultima["open"] and anterior["close"] < anterior["open"]:
                    return par, "put", 9

        # =========================
        # ⚡ ESTRATEGIA 3 (MOMENTUM)
        # =========================
        if cuerpo1 > cuerpo2 > cuerpo3:

            if ultima["close"] > ultima["open"] and anterior["close"] > anterior["open"]:
                return par, "call", 8

            if ultima["close"] < ultima["open"] and anterior["close"] < anterior["open"]:
                return par, "put", 8

        # =========================
        # 🧠 ESTRATEGIA 4 (PRICE ACTION)
        # =========================

        # 🔹 Rechazo alcista (mecha inferior larga)
        mecha_inferior = ultima["open"] - ultima["min"] if ultima["close"] >= ultima["open"] else ultima["close"] - ultima["min"]
        cuerpo = abs(ultima["close"] - ultima["open"])

        # 🔹 Rechazo bajista (mecha superior larga)
        mecha_superior = ultima["max"] - ultima["close"] if ultima["close"] >= ultima["open"] else ultima["max"] - ultima["open"]

        # 🟢 Compra por rechazo
        if (
            mecha_inferior > cuerpo * 1.5 and
            ultima["close"] > ultima["open"] and
            anterior["close"] > anterior["open"]
        ):
            return par, "call", 7

        # 🔴 Venta por rechazo
        if (
            mecha_superior > cuerpo * 1.5 and
            ultima["close"] < ultima["open"] and
            anterior["close"] < anterior["open"]
        ):
            return par, "put", 7

    return None
