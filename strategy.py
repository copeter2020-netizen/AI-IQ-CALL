import time
import numpy as np

ultima_operacion = 0

def detectar_entrada(velas):
    global ultima_operacion

    try:
        if len(velas) < 50:
            return None

        ahora = time.time()

        # 🔒 1 operación cada 45–90 min (ultra selectivo)
        if ahora - ultima_operacion < 2700:
            return None

        # ==========================
        # 📊 DATOS
        # ==========================
        closes = np.array([float(v["close"]) for v in velas])
        opens  = np.array([float(v["open"])  for v in velas])
        highs  = np.array([float(v["max"])   for v in velas])
        lows   = np.array([float(v["min"])   for v in velas])

        v = velas[-1]
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
        # 🔥 1) EVITAR RANGO (mercado muerto)
        # ==========================
        rango_total = max(highs[-20:]) - min(lows[-20:])
        volatilidad = np.mean(highs[-20:] - lows[-20:])

        if rango_total < volatilidad * 1.2:
            return None  # lateral

        # ==========================
        # 🔥 2) TENDENCIA REAL (línea)
        # ==========================
        pendiente = np.polyfit(range(20), closes[-20:], 1)[0]

        tendencia_alcista = pendiente > 0
        tendencia_bajista = pendiente < 0

        # ==========================
        # 🔥 3) FUERZA (vela actual)
        # ==========================
        fuerza_alcista = c > o and cuerpo > rango * 0.65
        fuerza_bajista = c < o and cuerpo > rango * 0.65

        # ==========================
        # 🔥 4) AGOTAMIENTO / MANIPULACIÓN
        # ==========================
        fake_up = mecha_sup > cuerpo * 1.5
        fake_down = mecha_inf > cuerpo * 1.5

        # ==========================
        # 🔥 5) CONTINUIDAD REAL (últimas velas)
        # ==========================
        secuencia = 0
        for i in range(-5, 0):
            if velas[i]["close"] > velas[i]["open"]:
                secuencia += 1
            else:
                secuencia -= 1

        continuidad_up = secuencia >= 4
        continuidad_down = secuencia <= -4

        # ==========================
        # 🔥 6) CONFIRMACIÓN DOBLE (línea + velas)
        # ==========================
        if (
            tendencia_alcista and
            continuidad_up and
            fuerza_alcista and
            not fake_up
        ):
            ultima_operacion = ahora
            return "call"

        if (
            tendencia_bajista and
            continuidad_down and
            fuerza_bajista and
            not fake_down
        ):
            ultima_operacion = ahora
            return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
