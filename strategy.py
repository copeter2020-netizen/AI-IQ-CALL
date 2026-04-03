import time
import pandas as pd


def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()


def RSI(series, period=14):
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def detectar_entrada(iq, par):
    try:
        velas = iq.get_candles(par, 60, 120, time.time())

        if not velas or len(velas) < 60:
            return None, None

        df = pd.DataFrame(velas)
        df = df.rename(columns={"max": "high", "min": "low"})

        close = df["close"]
        open_ = df["open"]
        high = df["high"]
        low = df["low"]

        ema20 = EMA(close, 20)
        ema50 = EMA(close, 50)
        rsi = RSI(close)

        precio = close.iloc[-1]
        apertura = open_.iloc[-1]
        maximo = high.iloc[-1]
        minimo = low.iloc[-1]

        cuerpo = abs(precio - apertura)
        rango = maximo - minimo

        # 🔥 FILTRO VELA
        vela_fuerte = cuerpo > (rango * 0.6)

        # 🔥 MECHAS (RECHAZO REAL)
        mecha_superior = maximo - max(precio, apertura)
        mecha_inferior = min(precio, apertura) - minimo

        rechazo_compra = mecha_inferior > cuerpo
        rechazo_venta = mecha_superior > cuerpo

        # 🔥 TENDENCIA FUERTE
        distancia_ema = abs(ema20.iloc[-1] - ema50.iloc[-1])

        tendencia_alcista = ema20.iloc[-1] > ema50.iloc[-1] and distancia_ema > 0.00005
        tendencia_bajista = ema20.iloc[-1] < ema50.iloc[-1] and distancia_ema > 0.00005

        # 🔥 SOPORTE / RESISTENCIA
        resistencia = high.iloc[-20:].max()
        soporte = low.iloc[-20:].min()

        cerca_resistencia = precio >= resistencia * 0.999
        cerca_soporte = precio <= soporte * 1.001

        # 🔥 VOLATILIDAD
        volatilidad = high.iloc[-10:].max() - low.iloc[-10:].min()

        if volatilidad < 0.00008:
            return None, None

        # =========================
        # 🔺 CALL (ULTRA FILTRADO)
        # =========================
        if (
            tendencia_alcista and
            rsi.iloc[-1] < 25 and
            cerca_soporte and
            rechazo_compra and
            vela_fuerte
        ):
            return "call", {"tipo": "call"}

        # =========================
        # 🔻 PUT (ULTRA FILTRADO)
        # =========================
        if (
            tendencia_bajista and
            rsi.iloc[-1] > 75 and
            cerca_resistencia and
            rechazo_venta and
            vela_fuerte
        ):
            return "put", {"tipo": "put"}

        return None, None

    except Exception as e:
        print(f"❌ ERROR STRATEGY: {e}")
        return None, None
