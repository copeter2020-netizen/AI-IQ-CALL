import numpy as np

def volatilidad_baja(df):
    ultimas = df.iloc[-10:]
    rangos = [v["max"] - v["min"] for _, v in ultimas.iterrows()]
    return np.mean(rangos) < (max(rangos) * 0.5)


def sobre_extension(df):
    mov = abs(df["close"].iloc[-1] - df["close"].iloc[-6])
    rango = max(df["max"][-20:]) - min(df["min"][-20:])
    return mov > rango * 0.7


def tendencia_fuerte(df):
    ultimas = df.iloc[-6:]
    verdes = sum(ultimas["close"] > ultimas["open"])
    rojas = sum(ultimas["close"] < ultimas["open"])
    return verdes >= 5 or rojas >= 5


def mechas_peligrosas(df):
    v = df.iloc[-1]
    cuerpo = abs(v["close"] - v["open"])
    mecha_sup = v["max"] - max(v["open"], v["close"])
    mecha_inf = min(v["open"], v["close"]) - v["min"]

    return mecha_sup > cuerpo * 2 or mecha_inf > cuerpo * 2


def mercado_lento(df):
    ultimas = df.iloc[-5:]
    return all(abs(v["close"] - v["open"]) < (v["max"] - v["min"]) * 0.3 for _, v in ultimas.iterrows())
