import pandas as pd


# ==========================
# INDICADORES
# ==========================
def bollinger(df, period=20):
    ma = df["close"].rolling(period).mean()
    std = df["close"].rolling(period).std()
    upper = ma + (2 * std)
    lower = ma - (2 * std)
    return upper, lower


def atr(df, period=14):
    df["tr"] = df["max"] - df["min"]
    return df["tr"].rolling(period).mean()


def stochastic(df, k_period=14):
    low_min = df["min"].rolling(k_period).min()
    high_max = df["max"].rolling(k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    return k


def fuerza(c):
    cuerpo = abs(c["close"] - c["open"])
    rango = c["max"] - c["min"]
    if rango == 0:
        return 0
    return cuerpo / rango


# ==========================
# SOPORTE / RESISTENCIA
# ==========================
def soporte_resistencia(df):
    soporte = df["min"].rolling(20).min().iloc[-1]
    resistencia = df["max"].rolling(20).max().iloc[-1]
    return soporte, resistencia


# ==========================
# ESTRATEGIA
# ==========================
def analyze_market(candles, c5, c15):

    try:
        df = pd.DataFrame(candles)

        if len(df) < 30:
            return None

        df["bb_upper"], df["bb_lower"] = bollinger(df)
        df["atr"] = atr(df)
        df["stoch"] = stochastic(df)

        soporte, resistencia = soporte_resistencia(df)

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # ==========================
        # FILTRO SOPORTE/RESISTENCIA
        # ==========================
        rango_sr = (resistencia - soporte) * 0.1

        if abs(last["close"] - soporte) < rango_sr:
            return None

        if abs(last["close"] - resistencia) < rango_sr:
            return None

        # ==========================
        # CONTINUIDAD + FUERZA
        # ==========================
        if not (last["close"] > prev["close"] or last["close"] < prev["close"]):
            return None

        if fuerza(last) < 0.5:
            return None

        # ==========================
        # ATR (VOLATILIDAD)
        # ==========================
        if last["atr"] < df["atr"].mean():
            return None

        # ==========================
        # STOCHASTIC
        # ==========================
        if last["stoch"] > 80:
            action = "put"
        elif last["stoch"] < 20:
            action = "call"
        else:
            return None

        # ==========================
        # BOLLINGER
        # ==========================
        if action == "call":
            if last["close"] < last["bb_lower"]:
                return None
        else:
            if last["close"] > last["bb_upper"]:
                return None

        # ==========================
        # TODAS LAS CONDICIONES
        # ==========================
        return {
            "action": action,
            "score": 10
        }

    except:
        return None
