import time
import pandas as pd

# 🔥 MODELO IA (PESOS)
modelo = {
    "tendencia": 1.0,
    "momento": 1.0,
    "rsi": 1.0,
    "volatilidad": 1.0
}


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

        if not velas or len(velas) < 40:
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
        # 🔥 FEATURES IA
        # =========================

        tendencia = 1 if ema20.iloc[-1] > ema50.iloc[-1] else -1
        momento = 1 if vela_verde else -1
        fuerza_rsi = 1 if rsi.iloc[-1] > 50 else -1

        volatilidad = high.iloc[-5:].max() - low.iloc[-5:].min()

        # filtro lateral
        if volatilidad < 0.00005:
            return None, None

        # =========================
        # 🧠 SISTEMA DE PUNTUACIÓN
        # =========================

        score_call = 0
        score_put = 0

        if tendencia == 1:
            score_call += modelo["tendencia"]
        else:
            score_put += modelo["tendencia"]

        if momento == 1:
            score_call += modelo["momento"]
        else:
            score_put += modelo["momento"]

        if fuerza_rsi == 1:
            score_call += modelo["rsi"]
        else:
            score_put += modelo["rsi"]

        if volatilidad > 0.0001:
            score_call += modelo["volatilidad"]
            score_put += modelo["volatilidad"]

        # =========================
        # 🎯 DECISIÓN FINAL
        # =========================

        if score_call > score_put and score_call >= 2:
            return "call", {
                "score": score_call,
                "tipo": "call"
            }

        if score_put > score_call and score_put >= 2:
            return "put", {
                "score": score_put,
                "tipo": "put"
            }

        return None, None

    except Exception as e:
        print(f"❌ ERROR IA: {e}")
        return None, None


def actualizar_modelo(features, resultado):
    global modelo

    if not features:
        return

    # 🔥 APRENDIZAJE POR REFUERZO REAL
    if resultado > 0:
        modelo["tendencia"] += 0.02
        modelo["momento"] += 0.02
        modelo["rsi"] += 0.02
    else:
        modelo["tendencia"] -= 0.02
        modelo["momento"] -= 0.02
        modelo["rsi"] -= 0.02

    # 🔒 LIMITES ESTABLES
    for key in modelo:
        modelo[key] = max(0.5, min(2.0, modelo[key]))

    print(f"🧠 MODELO IA: {modelo}")
