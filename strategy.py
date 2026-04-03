import time
import numpy as np

ultima_operacion = 0

def detectar_entrada(velas):
    global ultima_operacion

    try:
        if len(velas) < 100:
            return None

        ahora = time.time()

        # 🔒 ULTRA SELECTIVO (1 cada 2–4 horas)
        if ahora - ultima_operacion < 7200:
            return None

        # ⏱️ SOLO AL FINAL DE LA VELA
        if int(ahora) % 60 < 58:
            return None

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,h2,l2 = d(v2)
        o3,c3,_,_   = d(v3)

        rango = h1 - l1
        if rango == 0:
            return None

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        # ==========================
        # 🔥 1. MEJOR PAR (VOLATILIDAD REAL)
        # ==========================
        volatilidad = np.mean(highs[-20:] - lows[-20:])
        volatilidad_lenta = np.mean(highs[-50:] - lows[-50:])

        if volatilidad < volatilidad_lenta * 0.8:
            return None  # par muerto

        # ==========================
        # 🔥 2. EVITAR LATERAL
        # ==========================
        rango_total = max(highs[-25:]) - min(lows[-25:])
        if rango_total < volatilidad * 1.5:
            return None

        # ==========================
        # 🔥 3. SOPORTE / RESISTENCIA
        # ==========================
        resistencia = max(highs[-30:])
        soporte = min(lows[-30:])

        if abs(c1 - resistencia) < rango * 1.5:
            return None

        if abs(c1 - soporte) < rango * 1.5:
            return None

        # ==========================
        # 🔥 4. ESTRUCTURA REAL
        # ==========================
        estructura_up = highs[-1] > highs[-6] and lows[-1] > lows[-6]
        estructura_down = highs[-1] < highs[-6] and lows[-1] < lows[-6]

        # ==========================
        # 🔥 5. TENDENCIA + ACELERACIÓN
        # ==========================
        p1 = np.polyfit(range(30), closes[-30:], 1)[0]
        p2 = np.polyfit(range(10), closes[-10:], 1)[0]

        alcista = p2 > p1 > 0
        bajista = p2 < p1 < 0

        # ==========================
        # 🔥 6. PULLBACK LIMPIO
        # ==========================
        pullback_up = c2 < o2 and c2 > closes[-6]
        pullback_down = c2 > o2 and c2 < closes[-6]

        # ==========================
        # 🔥 7. CONTINUACIÓN PERFECTA
        # ==========================
        cont_up = (
            c1 > o1 and
            cuerpo > rango * 0.8 and
            mecha_sup < cuerpo * 0.2
        )

        cont_down = (
            c1 < o1 and
            cuerpo > rango * 0.8 and
            mecha_inf < cuerpo * 0.2
        )

        # ==========================
        # 🔥 8. RUPTURA REAL
        # ==========================
        break_up = c1 > h2
        break_down = c1 < l2

        # ==========================
        # 🔥 9. PRESIÓN FINAL
        # ==========================
        presion_up = c1 >= (h1 - rango * 0.15)
        presion_down = c1 <= (l1 + rango * 0.15)

        # ==========================
        # 🔥 10. EVITAR MANIPULACIÓN
        # ==========================
        fake_up = mecha_sup > cuerpo
        fake_down = mecha_inf > cuerpo

        # ==========================
        # 🎯 ENTRADA FINAL
        # ==========================
        if (
            alcista and
            estructura_up and
            pullback_up and
            cont_up and
            break_up and
            presion_up and
            not fake_up
        ):
            ultima_operacion = ahora
            return "call"

        if (
            bajista and
            estructura_down and
            pullback_down and
            cont_down and
            break_down and
            presion_down and
            not fake_down
        ):
            ultima_operacion = ahora
            return "put"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
