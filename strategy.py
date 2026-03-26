def es_verde(c):
    return c["close"] > c["open"]


def fuerza(c):
    rango = c["max"] - c["min"]
    if rango == 0:
        return 0
    return abs(c["close"] - c["open"]) / rango


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 5:
            return None

        c1 = candles[-1]  # última vela cerrada
        c2 = candles[-2]
        c3 = candles[-3]

        # ==========================
        # 🔥 MICRO TENDENCIA ALCISTA
        # ==========================
        if c3["close"] >= c2["close"]:
            return None

        # ==========================
        # 🔥 SEGUNDA VELA VERDE
        # ==========================
        if not es_verde(c2):
            return None

        if not es_verde(c1):
            return None

        # evitar vela débil
        if fuerza(c1) < 0.5:
            return None

        # ==========================
        # ✅ SOLO COMPRA
        # ==========================
        return {
            "action": "call",
            "score": 10
        }

    except:
        return None
