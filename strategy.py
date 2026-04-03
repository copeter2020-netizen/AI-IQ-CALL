import time
import pandas as pd
import ta


def detectar_entrada(iq, par):

    try:
        velas = iq.get_candles(par, 5, 60, time.time())
    except Exception as e:
        print(f"❌ Error obteniendo velas: {e}")
        return None

    # 🔥 VALIDAR DATOS
    if not velas or len(velas) < 20:
        return None

    df = pd.DataFrame(velas)

    # 🔥 ORDENAR (MUY IMPORTANTE)
    df = df.sort_values(by="from").reset_index(drop=True)

    # 🔥 COLUMNAS SEGURAS
    try:
        close = df["close"].astype(float)
        high = df["max"].astype(float)
        low = df["min"].astype(float)
        open_ = df["open"].astype(float)
    except:
        return None

    # 🔥 INDICADORES
    try:
        bb = ta.volatility.BollingerBands(close)
        upper = bb.bollinger_hband()
        lower = bb.bollinger_lband()

        sar = ta.trend.PSARIndicator(high, low, close).psar()
    except Exception as e:
        print(f"❌ Error indicadores: {e}")
        return None

    # 🔥 EVITAR NaN
    if upper.isna().iloc[-1] or lower.isna().iloc[-1] or sar.isna().iloc[-1]:
        return None

    last = -1
    prev = -2

    precio = close.iloc[last]
    apertura = open_.iloc[last]

    vela_prev_cierre = close.iloc[prev]
    vela_prev_apertura = open_.iloc[prev]

    # 🔻 PUT
    if (
        sar.iloc[last] > precio and
        lower.iloc[last] < precio < upper.iloc[last] and
        vela_prev_cierre > vela_prev_apertura and
        precio > apertura
    ):
        return "put"

    # 🔺 CALL
    if (
        sar.iloc[last] < precio and
        lower.iloc[last] < precio < upper.iloc[last] and
        vela_prev_cierre < vela_prev_apertura and
        precio < apertura
    ):
        return "call"

    return None
