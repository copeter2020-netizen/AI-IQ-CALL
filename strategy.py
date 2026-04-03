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
        velas = iq.get_candles(par, 60, 60, time.time())

        if not velas or len(velas) < 50:
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

        vela_verde = precio > apertura
        vela_roja = precio < apertura

        # =========================
        # 🔥 TENDENCIA
        # =========================
        tendencia_alcista = ema20.iloc[-1] > ema50.iloc[-1]
        tendencia_bajista = ema20.iloc[-1] < ema50.iloc[-1]

        # =========================
        # 🔥 SOPORTE / RESISTENCIA SIMPLE
        # =========================
        resistencia = high.iloc[-10:].max()
        soporte = low.iloc[-10:].min()

        cerca_resistencia = precio >= resistencia * 0.999
        cerca_soporte = precio <= soporte * 1.001

        # =========================
        # 🔥 CALL (TODO AL MISMO TIEMPO)
        # =========================
        if (
            tendencia_alcista and
            rsi.iloc[-1] > 55 and
            vela_verde and
            cerca_soporte
        ):
            return "call", {"tipo": "call"}

        # =========================
        # 🔥 PUT (TODO AL MISMO TIEMPO)
        # =========================
        if (
            tendencia_bajista and
            rsi.iloc[-1] < 45 and
            vela_roja and
            cerca_resistencia
        ):
            return "put", {"tipo": "put"}

        return None, None

    except Exception as e:
        print(f"❌ ERROR STRATEGY: {e}")
        return None, None
