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
        # 🔥 Velas 1 minuto (análisis fuerte)
        velas = iq.get_candles(par, 60, 80, time.time())

        if not velas or len(velas) < 50:
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

        # =========================
        # 📊 INDICADORES
        # =========================
        ema_20 = EMA(close, 20)
        ema_50 = EMA(close, 50)
        rsi = RSI(close, 14)

        precio = close.iloc[-1]
        apertura = open_.iloc[-1]

        vela_actual_verde = precio > apertura
        vela_actual_roja = precio < apertura

        vela_anterior_verde = close.iloc[-2] > open_.iloc[-2]
        vela_anterior_roja = close.iloc[-2] < open_.iloc[-2]

        # =========================
        # 📈 TENDENCIA FUERTE
        # =========================
        tendencia_alcista = ema_20.iloc[-1] > ema_50.iloc[-1]
        tendencia_bajista = ema_20.iloc[-1] < ema_50.iloc[-1]

        # =========================
        # 🔥 ZONAS (LIQUIDEZ)
        # =========================
        resistencia = high.iloc[-20:].max()
        soporte = low.iloc[-20:].min()

        # =========================
        # 🔥 VOLATILIDAD (FILTRO)
        # =========================
        rango = high.iloc[-10:].max() - low.iloc[-10:].min()

        if rango < 0.00005:
            return None, None  # mercado sin movimiento

        # =========================
        # 🚀 CALL (RUPTURA + CONFIRMACIÓN)
        # =========================
        if (
            tendencia_alcista and
            vela_anterior_roja and
            vela_actual_verde and
            precio > ema_20.iloc[-1] and
            precio > (resistencia * 0.998) and
            rsi.iloc[-1] > 55
        ):
            return "call", 3

        # =========================
        # 🚀 PUT (RUPTURA + CONFIRMACIÓN)
        # =========================
        if (
            tendencia_bajista and
            vela_anterior_verde and
            vela_actual_roja and
            precio < ema_20.iloc[-1] and
            precio < (soporte * 1.002) and
            rsi.iloc[-1] < 45
        ):
            return "put", 3

        # =========================
        # 🔥 REVERSIÓN FUERTE (EXTREMOS)
        # =========================

        if rsi.iloc[-1] > 80 and vela_actual_roja:
            return "put", 3

        if rsi.iloc[-1] < 20 and vela_actual_verde:
            return "call", 3

        return None, None

    except Exception as e:
        print(f"❌ ERROR ESTRATEGIA: {e}")
        return None, None
