def detectar_entrada_oculta(data):

    for par, velas in data.items():

        if len(velas) < 10:
            continue

        ultima = velas[-1]
        anterior = velas[-2]

        # tendencia simple
        tendencia_alcista = ultima["close"] > anterior["close"]
        tendencia_bajista = ultima["close"] < anterior["close"]

        # confirmación
        fuerza = abs(ultima["close"] - ultima["open"])

        if fuerza < 0.0001:
            continue

        if tendencia_alcista:
            return par, "call", 10

        if tendencia_bajista:
            return par, "put", 10

    return None
