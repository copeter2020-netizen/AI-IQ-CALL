import time
import pandas as pd


def detectar_entrada(iq, par):
    try:
        # 🔥 Obtener velas (1 minuto)
        velas = iq.get_candles(par, 60, 30, time.time())

        if not velas or len(velas) < 5:
            return None, None

        df = pd.DataFrame(velas)

        # Asegurar columnas correctas
        df = df.rename(columns={
            "max": "high",
            "min": "low"
        })

        close = df["close"]
        open_ = df["open"]
        high = df["high"]
        low = df["low"]

        # Últimas velas
        ultima = close.iloc[-1]
        apertura = open_.iloc[-1]

        anterior_close = close.iloc[-2]
        anterior_open = open_.iloc[-2]

        # 🔥 FILTRO DE TENDENCIA SIMPLE
        tendencia_alcista = close.iloc[-3:].mean() > close.iloc[-6:-3].mean()
        tendencia_bajista = close.iloc[-3:].mean() < close.iloc[-6:-3].mean()

        # 🔥 SOPORTE / RESISTENCIA SIMPLE
        soporte = low.min()
        resistencia = high.max()

        # =========================
        # 📈 SEÑAL CALL
        # =========================
        if (
            tendencia_alcista and
            anterior_close < anterior_open and  # vela roja antes
            ultima > apertura and              # vela actual verde
            ultima > soporte
        ):
            return "call", 1

        # =========================
        # 📉 SEÑAL PUT
        # =========================
        if (
            tendencia_bajista and
            anterior_close > anterior_open and  # vela verde antes
            ultima < apertura and              # vela actual roja
            ultima < resistencia
        ):
            return "put", 1

        return None, None

    except Exception as e:
        print(f"❌ ERROR ESTRATEGIA: {e}")
        return None, None
