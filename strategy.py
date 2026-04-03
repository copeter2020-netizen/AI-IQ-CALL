import numpy as np

def ema(data, period=20):
    ema_values = []
    k = 2 / (period + 1)

    for i in range(len(data)):
        if i < period:
            ema_values.append(np.mean(data[:i+1]))
        else:
            ema_values.append(data[i] * k + ema_values[-1] * (1 - k))

    return ema_values


def detectar_soporte_resistencia(candles):
    closes = [c['close'] for c in candles]

    soporte = min(closes[-20:])
    resistencia = max(closes[-20:])

    return soporte, resistencia


def fuerza_vela(candle):
    cuerpo = abs(candle['close'] - candle['open'])
    rango = candle['max'] - candle['min']

    if rango == 0:
        return 0

    return cuerpo / rango


# ✅ SOLO RECIBE 1 PARÁMETRO (candles)
def detectar_entrada(candles):

    if len(candles) < 30:
        return None

    closes = [c['close'] for c in candles]
    ema20 = ema(closes, 20)

    ultima = candles[-1]
    anterior = candles[-2]

    soporte, resistencia = detectar_soporte_resistencia(candles)

    fuerza = fuerza_vela(ultima)

    precio = ultima['close']
    tendencia = "alcista" if precio > ema20[-1] else "bajista"

    # ==========================
    # LÓGICA
    # ==========================

    if precio <= soporte + 0.0002:
        if fuerza > 0.5 and ultima['close'] > ultima['open']:
            return "call", 1

    if precio >= resistencia - 0.0002:
        if fuerza > 0.5 and ultima['close'] < ultima['open']:
            return "put", 1

    if tendencia == "alcista":
        if ultima['close'] > anterior['close'] and fuerza > 0.6:
            return "call", 1

    if tendencia == "bajista":
        if ultima['close'] < anterior['close'] and fuerza > 0.6:
            return "put", 1

    return None
