import time
import pandas as pd


def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()


def RSI(series, period=14):
    delta = series.diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    return 100 - (100 / (1 + rs))


def detectar_entrada(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        if not velas or len(velas) < 30:
            return None, None

        df = pd.DataFrame(velas)

        df = df.rename(columns={
            "max": "high",
            "min": "low"
        })

        close = df["close"]
        open_ = df["open"]
        high = df["high"]
        low = df["low"]

        ema_20 = EMA(close, 20)
        ema_50 = EMA(close, 50)
        rsi = RSI(close, 14)

        precio = close.iloc[-1]
        apertura = open_.iloc[-1]

        vela_verde = precio > apertura
        vela_roja = precio < apertura

        tendencia_alcista = ema_20.iloc[-1] > ema_50.iloc[-1]
        tendencia_bajista = ema_20.iloc[-1] < ema_50.iloc[-1]

        resistencia = high.iloc[-20:].max()
        soporte = low.iloc[-20:].min()

        # =========================
        # 🚀 ENTRADAS PRINCIPALES
        # =========================

        if (
            tendencia_alcista and
            vela_verde and
            precio > ema_20.iloc[-1] and
            rsi.iloc[-1] > 55
        ):
            return "call", 1

        if (
            tendencia_bajista and
            vela_roja and
            precio < ema_20.iloc[-1] and
            rsi.iloc[-1] < 45
        ):
            return "put", 1

        # =========================
        # 🔥 SOBRECOMPRA
        # =========================
        if rsi.iloc[-1] > 75 and vela_roja and precio >= resistencia * 0.995:
            return "put", 1

        # =========================
        # 🔥 SOBREVENTA
        # =========================
        if rsi.iloc[-1] < 25 and vela_verde and precio <= soporte * 1.005:
            return "call", 1

        return None, None

    except Exception as e:
        print(f"❌ ERROR ESTRATEGIA: {e}")
        return None, None
