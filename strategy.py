import pandas as pd


# ==========================
# INDICADORES
# ==========================
def ema(df, period=50):
    df["ema"] = df["close"].ewm(span=period).mean()


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


# ==========================
# KDJ
# ==========================
def kdj(df, period=9):

    low_min = df["min"].rolling(period).min()
    high_max = df["max"].rolling(period).max()

    rsv = (df["close"] - low_min) / (high_max - low_min) * 100

    df["K"] = rsv.ewm(com=2).mean()
    df["D"] = df["K"].ewm(com=2).mean()
    df["J"] = 3 * df["K"] - 2 * df["D"]


# ==========================
# 🔥 RVI (Relative Vigor Index)
# ==========================
def rvi(df, period=10):

    close_open = df["close"] - df["open"]
    high_low = df["max"] - df["min"]

    num = close_open.rolling(period).mean()
    den = high_low.rolling(period).mean()

    df["rvi"] = num / den
    df["rvi_signal"] = df["rvi"].rolling(4).mean()


def fuerza(c):
    rango = c["max"] - c["min"]
    if rango == 0:
        return 0
    return abs(c["close"] - c["open"]) / rango


# ==========================
# ESTRATEGIA PRO + KDJ + RVI
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 70:
            return None

        ema(df)
        bollinger(df)
        cci(df)
        kdj(df)
        rvi(df)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # ==========================
        # 🔥 TENDENCIA ALCISTA
        # ==========================
        if last["close"] < last["ema"]:
            return None

        # ==========================
        # 🔥 PULLBACK LIMPIO
        # ==========================
        if prev["close"] > prev["open"]:
            return None

        # ==========================
        # 🔥 BOLLINGER
        # ==========================
        if prev["close"] > prev["bb_lower"]:
            return None

        # ==========================
        # 🔥 CCI
        # ==========================
        if prev["cci"] > -100:
            return None

        # ==========================
        # 🔥 KDJ
        # ==========================
        if not (
            prev["K"] < prev["D"] and
            last["K"] > last["D"] and
            last["K"] < 30
        ):
            return None

        # ==========================
        # 🔥 RVI CONFIRMACIÓN
        # ==========================
        # cruce alcista + momentum positivo
        if not (
            prev["rvi"] < prev["rvi_signal"] and
            last["rvi"] > last["rvi_signal"] and
            last["rvi"] > 0
        ):
            return None

        # ==========================
        # 🔥 VELA FUERTE
        # ==========================
        if last["close"] <= last["open"]:
            return None

        if fuerza(last) < 0.6:
            return None

        # ==========================
        # 🔥 EVITAR LATERALIDAD
        # ==========================
        rango = df["close"].rolling(10).max().iloc[-1] - df["close"].rolling(10).min().iloc[-1]

        if rango < 0.0005:
            return None

        return {
            "action": "call",
            "score": 10
        }

    except:
        return None
