import pandas as pd

def stochastic(df):
    low_min = df["min"].rolling(8).min()
    high_max = df["max"].rolling(8).max()

    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    k = k.rolling(3).mean()
    d = k.rolling(3).mean()

    return k, d


def detectar_mejor_entrada(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        df = pd.DataFrame(velas)

        if len(df) < 50:
            continue

        soporte = df["min"].rolling(20).min().iloc[-1]
        resistencia = df["max"].rolling(20).max().iloc[-1]

        v = df.iloc[-1]

        rango = v["max"] - v["min"]
        if rango == 0:
            continue

        cuerpo = abs(v["close"] - v["open"])
        mecha_sup = v["max"] - max(v["open"], v["close"])
        mecha_inf = min(v["open"], v["close"]) - v["min"]

        k, d = stochastic(df)

        if k.isna().iloc[-1] or d.isna().iloc[-1]:
            continue

        k1, d1 = k.iloc[-1], d.iloc[-1]
        k2, d2 = k.iloc[-2], d.iloc[-2]

        score = 0
        direccion = None

        # CALL
        if abs(v["min"] - soporte) < (resistencia - soporte) * 0.03:

            if k1 > 15:
                continue

            if k2 < d2 and k1 > d1:
                score += 30

            if mecha_inf > cuerpo * 1.5:
                score += 30

            if v["close"] > v["open"] and cuerpo > rango * 0.6:
                score += 30

            direccion = "call"

        # PUT
        elif abs(v["max"] - resistencia) < (resistencia - soporte) * 0.03:

            if k1 < 85:
                continue

            if k2 > d2 and k1 < d1:
                score += 30

            if mecha_sup > cuerpo * 1.5:
                score += 30

            if v["close"] < v["open"] and cuerpo > rango * 0.6:
                score += 30

            direccion = "put"

        else:
            continue

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 70:
        return mejor

    return None
