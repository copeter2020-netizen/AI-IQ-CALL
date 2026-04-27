import numpy as np

# ================================
# CONFIGURACIÓN
# ================================
MIN_BODY = 0.00015
WICK_RATIO = 2.5
TREND_CANDLES = 5


# ================================
# FUNCIONES BASE
# ================================

def body_size(candle):
    return abs(candle["close"] - candle["open"])


def candle_range(candle):
    return candle["max"] - candle["min"]


def is_doji(candle):
    body = body_size(candle)
    rango = candle_range(candle)

    if rango == 0:
        return True

    return body < (rango * 0.2)


def strong_bullish(candle):
    body = body_size(candle)
    rango = candle_range(candle)

    if candle["close"] <= candle["open"]:
        return False

    if body < MIN_BODY:
        return False

    # cierre cerca del máximo
    if (candle["max"] - candle["close"]) > (body * 0.3):
        return False

    return True


def strong_bearish(candle):
    body = body_size(candle)
    rango = candle_range(candle)

    if candle["close"] >= candle["open"]:
        return False

    if body < MIN_BODY:
        return False

    # cierre cerca del mínimo
    if (candle["close"] - candle["min"]) > (body * 0.3):
        return False

    return True


# ================================
# DETECTAR TENDENCIA
# ================================

def get_trend(candles):
    closes = [c["close"] for c in candles[-TREND_CANDLES:]]

    if all(closes[i] > closes[i-1] for i in range(1, len(closes))):
        return "up"

    if all(closes[i] < closes[i-1] for i in range(1, len(closes))):
        return "down"

    return "range"


# ================================
# DETECTAR AGOTAMIENTO
# ================================

def is_exhaustion(candles):
    last = candles[-1]
    prev = candles[-2]

    # vela más pequeña que la anterior = debilidad
    if body_size(last) < body_size(prev) * 0.5:
        return True

    return False


# ================================
# ZONA DE REVERSIÓN SIMPLE
# ================================

def near_reversal_zone(candles):
    highs = [c["max"] for c in candles[-10:]]
    lows = [c["min"] for c in candles[-10:]]

    last = candles[-1]

    # cerca de resistencia
    if last["close"] >= max(highs) * 0.999:
        return True

    # cerca de soporte
    if last["close"] <= min(lows) * 1.001:
        return True

    return False


# ================================
# FUNCIÓN PRINCIPAL
# ================================

def check_signal(candles):
    if len(candles) < 20:
        return None

    last = candles[-1]

    # ❌ FILTROS DUROS
    if is_doji(last):
        return None

    if is_exhaustion(candles):
        return None

    if near_reversal_zone(candles):
        return None

    trend = get_trend(candles)

    # ============================
    # CALL
    # ============================
    if trend == "up" and strong_bullish(last):
        return "call"

    # ============================
    # PUT
    # ============================
    if trend == "down" and strong_bearish(last):
        return "put"

    return None
