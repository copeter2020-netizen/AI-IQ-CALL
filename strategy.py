import pandas as pd


# ==========================
# INDICADORES
# ==========================
def bollinger(df, period=20):
    ma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    df["bb_upper"] = ma + (2 * std)
    df["bb_lower"] = ma - (2 * std)


def cci(df, period=20):
    tp = (df["max"] + df["min"] + df["close"]) / 3
    ma = tp.rolling(period).mean()
    md = (tp - ma).abs().rolling(period).mean()
    df["cci"] = (tp - ma) / (0.015 * md)


def fuerza(c):
    rango = c["max"] - c["min"]
    if rango == 0:
        return 0
    return abs(c["close"] - c["open"]) / rango


# ==========================
# ESTRATEGIA
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 25:
            return None

        bollinger(df)
        cci(df)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # ==========================
        # 🔥 CONDICIONES
        # ==========================

        # vela verde
        if last["close"] <= last["open"]:
            return None

        # fuerza
        if fuerza(last) < 0.5:
            return None

        # bollinger (rebote inferior)
        if last["close"] < last["bb_lower"]:
            return None

        # CCI (salida de sobreventa)
        if last["cci"] < -100:
            return None

        # confirmación vela anterior
        if prev["close"] <= prev["open"]:
            return None

        return {
            "action": "call",
            "score": 10
        }

    except:
        return None
