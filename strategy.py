import time

ultima_operacion = 0

def detectar_entrada(velas):
    global ultima_operacion

    try:
        if len(velas) < 30:
            return None

        ahora = time.time()

        # 🔥 ultra filtro (1 operación cada 30 min)
        if ahora - ultima_operacion < 1800:
            return None

        v = velas[-1]
        v_prev = velas[-2]

        o = float(v["open"])
        c = float(v["close"])
        h = float(v["max"])
        l = float(v["min"])

        cuerpo = abs(c - o)
        rango = h - l

        if rango == 0:
            return None

        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        # ==========================
        # 🔥 FUERZA REAL
        # ==========================
        fuerza_alcista = c > o and cuerpo > rango * 0.6
        fuerza_bajista = c < o and cuerpo > rango * 0.6

        # ==========================
        # 🔄 AGOTAMIENTO
        # ==========================
        agotamiento_alcista = mecha_sup > cuerpo * 1.5
        agotamiento_bajista = mecha_inf > cuerpo * 1.5

        # ==========================
        # 📊 CONTEXTO
        # ==========================
        tendencia = 0
        for i in range(-5, 0):
            if velas[i]["close"] > velas[i]["open"]:
                tendencia += 1
            else:
                tendencia -= 1

        # ==========================
        # 🎯 FILTRO EXTREMO
        # ==========================
        if fuerza_alcista and tendencia > 3 and not agotamiento_alcista:
            ultima_operacion = ahora
            return "call"

        if fuerza_bajista and tendencia < -3 and not agotamiento_bajista:
            ultima_operacion = ahora
            return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
