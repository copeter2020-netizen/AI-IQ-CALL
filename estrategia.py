import pandas as pd

# ==============================
# 🔥 INDICADOR TII (REAL)
# ==============================

def calculate_indicators(df):
    try:
        close = df["close"]

        period = 60

        # Media móvil
        ma = close.rolling(period).mean()

        # Diferencia
        diff = close - ma

        # Separar positivos y negativos
        positive = diff.clip(lower=0)
        negative = (-diff).clip(lower=0)

        sum_pos = positive.rolling(period).sum()
        sum_neg = negative.rolling(period).sum()

        # Evitar división por cero
        tii = 100 * (sum_pos / (sum_pos + sum_neg + 1e-9))

        df["tii"] = tii

        return df

    except Exception as e:
        print("Error en indicadores:", e)
        return df


# ==============================
# 🎯 SEÑALES
# ==============================

def check_signal(df):
    try:
        if "tii" not in df.columns:
            return None

        # Asegurar suficientes datos
        if len(df) < 3:
            return None

        prev = df["tii"].iloc[-2]
        curr = df["tii"].iloc[-1]

        # 🟢 CALL → cruza desde abajo 20 hacia arriba
        if prev < 20 and curr > 20:
            return "call"

        # 🔴 PUT → cruza desde arriba 80 hacia abajo
        if prev > 80 and curr < 80:
            return "put"

        return None

    except Exception as e:
        print("Error en señal:", e)
        return None
