import time

ultima_operacion = 0

def patron_repetido(velas):
    try:
        # comparar últimas 5 velas con anteriores
        actual = velas[-5:]
        anterior = velas[-10:-5]

        coincidencias = 0

        for i in range(5):
            dir_actual = actual[i]["close"] > actual[i]["open"]
            dir_anterior = anterior[i]["close"] > anterior[i]["open"]

            if dir_actual == dir_anterior:
                coincidencias += 1

        return coincidencias >= 4

    except:
        return False


def detectar_entrada(velas):
    global ultima_operacion

    try:
        ahora = time.time()

        if len(velas) < 150:
            return None

        # ⛔ 1 operación cada 20 min
        if ahora - ultima_operacion < 1200:
            return None

        # 🔥 patrón repetido obligatorio
        if not patron_repetido(velas):
            return None

        v = velas[-1]

        o = float(v["open"])
        c = float(v["close"])
        h = float(v["max"])
        l = float(v["min"])

        cuerpo = abs(c - o)
        rango = h - l

        if rango == 0:
            return None

        # 🔥 vela perfecta extrema
        if cuerpo < rango * 0.95:
            return None

        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        # ⛔ cero oposición
        if mecha_sup > cuerpo * 0.1 or mecha_inf > cuerpo * 0.1:
            return None

        # 🔥 continuidad extrema
        velas_up = sum(1 for v in velas[-15:] if v["close"] > v["open"])
        velas_down = sum(1 for v in velas[-15:] if v["close"] < v["open"])

        if c > o and velas_up >= 13:
            ultima_operacion = ahora
            return "call"

        if c < o and velas_down >= 13:
            ultima_operacion = ahora
            return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
