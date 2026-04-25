import numpy as np

def calcular_tii(close_prices, periodo=20):
    if len(close_prices) < periodo:
        return None

    ma = np.mean(close_prices[-periodo:])
    diff = close_prices[-periodo:] - ma

    positivos = np.sum(diff[diff > 0]) if np.any(diff > 0) else 0
    negativos = abs(np.sum(diff[diff < 0])) if np.any(diff < 0) else 0

    if positivos + negativos == 0:
        return 50

    tii = (positivos / (positivos + negativos)) * 100
    return tii


def detectar_cruce(tii_actual, tii_anterior):
    señal = None
    fuerza = abs(tii_actual - tii_anterior)

    # CRUCE DESDE ABAJO (COMPRA)
    if tii_anterior < 20 and tii_actual > 20:
        señal = "call"

    # CRUCE DESDE ARRIBA (VENTA)
    elif tii_anterior > 80 and tii_actual < 80:
        señal = "put"

    return señal, fuerza


def detect_signal(candles):
    try:
        close_prices = np.array([c["close"] for c in candles])

        tii_actual = calcular_tii(close_prices)
        tii_anterior = calcular_tii(close_prices[:-1])

        if tii_actual is None or tii_anterior is None:
            return None

        señal, fuerza = detectar_cruce(tii_actual, tii_anterior)

        if señal:
            return {
                "signal": señal,
                "strength": fuerza,
                "tii": tii_actual
            }

        return None

    except Exception as e:
        print(f"❌ Error estrategia: {e}")
        return None
