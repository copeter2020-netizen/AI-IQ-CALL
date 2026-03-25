import pandas as pd


def contar_velas(candles):
    count = 0

    for i in range(len(candles)-1, -1, -1):
        c = candles[i]

        if c["close"] > c["open"]:
            count += 1
        else:
            break

    return count


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 5:
            return None

        # 🔥 contar continuidad verde
        continuidad = contar_velas(candles)

        # 🔥 SOLO 1, 2 o 3 velas verdes
        if continuidad < 1 or continuidad > 3:
            return None

        # 🔥 última vela debe ser verde
        last = candles[-1]
        if last["close"] <= last["open"]:
            return None

        # 🔥 fuerza de la vela
        cuerpo = abs(last["close"] - last["open"])
        rango = last["max"] - last["min"]

        if rango == 0:
            return None

        fuerza = cuerpo / rango

        # 🔥 filtro de calidad
        if fuerza < 0.4:
            return None

        # score según continuidad
        score = continuidad + 2

        return {
            "action": "call",
            "score": score,
            "continuidad": continuidad
        }

    except:
        return None
