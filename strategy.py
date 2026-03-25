import pandas as pd


def ema(values, period):
    return pd.Series(values).ewm(span=period).mean().tolist()


def fuerza_vela(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]

    if rango == 0:
        return 0

    return cuerpo / rango


def es_retroceso(c1, c2):
    # vela roja débil después de verde fuerte
    return (
        c1["close"] < c1["open"] and
        (abs(c1["close"] - c1["open"]) < abs(c2["close"] - c2["open"]))
    )


def analyze_market(candles, c5, c15):

    try:
        if len(candles) < 20:
            return None

        closes = [c["close"] for c in candles]

        ema20 = ema(closes, 20)
        ema8 = ema(closes, 8)

        last = candles[-1]
        prev = candles[-2]
        prev2 = candles[-3]

        # ==========================
        # FILTRO TENDENCIA
        # ==========================
        if closes[-1] < ema20[-1]:
            return None

        if ema8[-1] < ema20[-1]:
            return None

        # ==========================
        # ESTRUCTURA ALCISTA
        # ==========================
        if not (last["close"] > prev["close"]):
            return None

        # ==========================
        # RETROCESO INSTITUCIONAL
        # ==========================
        retroceso = es_retroceso(prev, prev2)

        # ==========================
        # CONTINUIDAD O REENTRADA
        # ==========================
        if not (
            # impulso directo
            (last["close"] > last["open"] and fuerza_vela(last) > 0.5)

            # o retroceso + ruptura
            or (
                retroceso and
                last["close"] > prev["open"]
            )
        ):
            return None

        # ==========================
        # EVITAR SOBRECOMPRA
        # ==========================
        rango = last["max"] - candles[-6]["min"]

        if rango > (last["max"] - last["min"]) * 5:
            return None

        # ==========================
        # SCORE INSTITUCIONAL
        # ==========================
        score = 0

        score += 2 if last["close"] > ema8[-1] else 0
        score += 2 if fuerza_vela(last) > 0.6 else 1
        score += 1 if retroceso else 0

        return {
            "action": "call",
            "score": score,
            "tipo": "institucional"
        }

    except:
        return None
