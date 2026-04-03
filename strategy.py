import time
import pandas as pd


def detectar_entrada(iq, par):

    # 🔥 30 MIN = 1800 segundos / 4s = 450 velas
    velas = iq.get_candles(par, 4, 450, time.time())
    df = pd.DataFrame(velas)

    if df.empty or len(df) < 50:
        return None, None

    close = df["close"]
    open_ = df["open"]
    high = df["max"]
    low = df["min"]

    # 🔥 ESTRUCTURA DEL MERCADO
    maximo = high.rolling(50).max()
    minimo = low.rolling(50).min()

    precio_actual = close.iloc[-1]

    resistencia = maximo.iloc[-2]
    soporte = minimo.iloc[-2]

    # 🔥 MOMENTUM
    velas_verdes = sum(close.iloc[-10:] > open_.iloc[-10:])
    velas_rojas = sum(close.iloc[-10:] < open_.iloc[-10:])

    # ==============================
    # 🔻 VENTA (PUT)
    # ==============================
    if precio_actual >= resistencia:

        if velas_rojas > velas_verdes:

            distancia = precio_actual - soporte

            # 🔥 tiempo dinámico
            if distancia > 0.002:
                expiracion = 3
            elif distancia > 0.001:
                expiracion = 2
            else:
                expiracion = 1

            return "put", expiracion

    # ==============================
    # 🔺 COMPRA (CALL)
    # ==============================
    if precio_actual <= soporte:

        if velas_verdes > velas_rojas:

            distancia = resistencia - precio_actual

            if distancia > 0.002:
                expiracion = 3
            elif distancia > 0.001:
                expiracion = 2
            else:
                expiracion = 1

            return "call", expiracion

    return None, None
