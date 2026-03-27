def body(c):
    return abs(c["close"] - c["open"])


def rango(c):
    return c["max"] - c["min"]


def fuerza(c):
    r = rango(c)
    if r == 0:
        return 0
    return body(c) / r


def mecha_superior(c):
    return c["max"] - max(c["close"], c["open"])


def mecha_inferior(c):
    return min(c["close"], c["open"]) - c["min"]


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 5:
            return None

        c1 = candles[-1]  # última vela
        c2 = candles[-2]
        c3 = candles[-3]

        # ==========================
        # 🔴 FAKE BREAK ARRIBA → PUT
        # ==========================
        if (
            c2["max"] > c3["max"] and                # rompe máximo
            c2["close"] < c3["max"] and             # cierra debajo (falso rompimiento)
            mecha_superior(c2) > body(c2) and       # rechazo fuerte
            c1["close"] < c1["open"] and            # confirmación roja
            fuerza(c1) > 0.5
        ):
            return {"action": "put", "score": 10}

        # ==========================
        # 🟢 FAKE BREAK ABAJO → CALL
        # ==========================
        if (
            c2["min"] < c3["min"] and               # rompe mínimo
            c2["close"] > c3["min"] and             # cierra arriba
            mecha_inferior(c2) > body(c2) and       # rechazo inferior
            c1["close"] > c1["open"] and            # confirmación verde
            fuerza(c1) > 0.5
        ):
            return {"action": "call", "score": 10}

        return None

    except:
        return None
