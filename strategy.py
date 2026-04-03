import time
import pandas as pd

# 🔥 MEMORIA DE IA
modelo = {
    "call": 0.5,
    "put": 0.5
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
        velas = iq.get_candles(par, 60, 50, time.time())

        if not velas or len(velas) < 30:
            return None, None

        df = pd.DataFrame(velas)
        df = df.rename(columns={"max": "high", "min": "low"})

        close = df["close"]

        ema = EMA(close, 20)
        rsi = RSI(close)

        precio = close.iloc[-1]

        # 🔥 FEATURES (lo que aprende la IA)
        features = {
            "precio": float(precio),
            "ema": float(ema.iloc[-1]),
            "rsi": float(rsi.iloc[-1])
        }

        # 🔥 FILTRO INTELIGENTE
        if 40 < features["rsi"] < 60:
            return None, None  # evita mercado lateral

        # 🔥 DECISIÓN ADAPTATIVA
        if modelo["call"] > modelo["put"]:
            decision = "call"
        else:
            decision = "put"

        return decision, features

    except Exception as e:
        print(f"❌ ERROR IA: {e}")
        return None, None


def actualizar_modelo(features, resultado):
    global modelo

    # 🔥 APRENDIZAJE EN TIEMPO REAL
    if resultado > 0:
        # refuerza decisión ganadora
        modelo["call"] += 0.02
        modelo["put"] -= 0.01
    else:
        # penaliza pérdida
        modelo["call"] -= 0.02
        modelo["put"] += 0.01

    # 🔒 LIMITES
    modelo["call"] = max(0.1, min(0.9, modelo["call"]))
    modelo["put"] = max(0.1, min(0.9, modelo["put"]))

    print(f"🧠 IA ACTUALIZADA: {modelo}")
