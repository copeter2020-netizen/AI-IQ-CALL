import time

ultima_operacion = 0
racha_perdidas = 0

def detectar_entrada(velas):
    global ultima_operacion, racha_perdidas

    try:
        if len(velas) < 40:
            return None

        # ==========================
        # 🧠 BLOQUEO POR RACHA
        # ==========================
        if racha_perdidas >= 2:
            print("⛔ Parado por racha negativa")
            return None

        # ==========================
        # 🧠 ESPACIADO ENTRE TRADES
        # ==========================
        ahora = time.time()

        if ahora - ultima_operacion < 60:
            return None

        v = velas[-1]
        v1 = velas[-2]

        o = float(v["open"])
        c = float(v["close"])
        h = float(v["max"])
        l = float(v["min"])

        cuerpo = abs(c - o)
        rango = h - l

        if rango == 0:
            return None

        # ==========================
        # 🔥 SOLO VELAS PERFECTAS
        # ==========================
        if cuerpo < rango * 0.7:
            return None

        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        # ==========================
        # 📊 CONTEXTO FUERTE
        # ==========================
        cierres = [v["close"] for v in velas[-20:]]

        tendencia_alcista = cierres[-1] > cierres[0]
        tendencia_bajista = cierres[-1] < cierres[0]

        volatilidad = max(cierres) - min(cierres)

        # ❌ NO MERCADO MUERTO
        if volatilidad < 0.0008:
            return None

        # ==========================
        # 🔥 CONSISTENCIA
        # ==========================
        velas_up = sum(1 for v in velas[-5:] if v["close"] > v["open"])
        velas_down = sum(1 for v in velas[-5:] if v["close"] < v["open"])

        # ==========================
        # 🔥 PRESIÓN
        # ==========================
        presion_compra = c > o and cuerpo > rango * 0.7
        presion_venta = c < o and cuerpo > rango * 0.7

        # ==========================
        # 🔄 RECHAZO
        # ==========================
        rechazo_venta = mecha_sup > cuerpo
        rechazo_compra = mecha_inf > cuerpo

        # ==========================
        # 🎯 ENTRADAS ULTRA SELECTIVAS
        # ==========================

        if (
            presion_compra and
            tendencia_alcista and
            velas_up >= 4 and
            not rechazo_venta
        ):
            ultima_operacion = ahora
            return "call"

        if (
            presion_venta and
            tendencia_bajista and
            velas_down >= 4 and
            not rechazo_compra
        ):
            ultima_operacion = ahora
            return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
