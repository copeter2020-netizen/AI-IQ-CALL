import time
import numpy as np

ultima_operacion = 0

def evaluar_movimiento(velas):
    try:
        if len(velas) < 120:
            return None

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)
        o2,c2,h2,l2 = d(v2)

        rango = h1 - l1
        if rango == 0:
            return None

        cuerpo = abs(c1 - o1)

        score = 0

        # ==========================
        # 🔥 1. DIRECCIÓN GENERAL
        # ==========================
        pendiente = np.polyfit(range(40), closes[-40:], 1)[0]

        if pendiente > 0:
            direccion = "call"
            score += 10
        elif pendiente < 0:
            direccion = "put"
            score += 10
        else:
            return None

        # ==========================
        # 🔥 2. ACELERACIÓN REAL
        # ==========================
        p1 = np.polyfit(range(20), closes[-20:], 1)[0]
        p2 = np.polyfit(range(10), closes[-10:], 1)[0]

        if direccion == "call" and p2 > p1:
            score += 15
        elif direccion == "put" and p2 < p1:
            score += 15
        else:
            return None

        # ==========================
        # 🔥 3. ENERGÍA DEL MOVIMIENTO
        # ==========================
        impulso = abs(closes[-1] - closes[-15])
        rango_prom = np.mean(highs[-20:] - lows[-20:])

        if impulso > rango_prom * 2:
            score += 15

        # ==========================
        # 🔥 4. NO SOBREEXTENDIDO
        # ==========================
        extension = abs(closes[-1] - closes[-30])

        if extension < rango_prom * 5:
            score += 10
        else:
            return None

        # ==========================
        # 🔥 5. CONTINUACIÓN (VELA ACTUAL)
        # ==========================
        if cuerpo > rango * 0.75:
            score += 15

        # ==========================
        # 🔥 6. PRESIÓN FINAL
        # ==========================
        if direccion == "call" and c1 >= h1 - rango * 0.2:
            score += 10
        elif direccion == "put" and c1 <= l1 + rango * 0.2:
            score += 10
        else:
            return None

        # ==========================
        # 🔥 7. RUPTURA
        # ==========================
        if direccion == "call" and c1 > h2:
            score += 15
        elif direccion == "put" and c1 < l2:
            score += 15
        else:
            return None

        return direccion, score

    except:
        return None


def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 7200:
        return None

    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        resultado = evaluar_movimiento(velas)

        if resultado:
            direccion, score = resultado

            if score > mejor_score:
                mejor_score = score
                mejor = (par, direccion, score)

    # 🔥 SOLO ENTRA SI ES CASI PERFECTO
    if mejor and mejor_score >= 90:
        ultima_operacion = ahora
        return mejor

    return None
