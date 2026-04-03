import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 CONTINUACIÓN (TENDENCIA)
# ==========================
def evaluar_continuacion(velas):
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

        # 🔥 estructura HH / HL o LL / LH
        hh = highs[-1] > highs[-5] > highs[-10]
        hl = lows[-1] > lows[-5] > lows[-10]

        ll = highs[-1] < highs[-5] < highs[-10]
        lh = lows[-1] < lows[-5] < lows[-10]

        if hh and hl:
            direccion = "call"
            score += 25
        elif ll and lh:
            direccion = "put"
            score += 25
        else:
            return None

        # 🔥 tendencia + aceleración
        p1 = np.polyfit(range(30), closes[-30:], 1)[0]
        p2 = np.polyfit(range(10), closes[-10:], 1)[0]

        if direccion == "call" and p2 > p1 > 0:
            score += 15
        elif direccion == "put" and p2 < p1 < 0:
            score += 15
        else:
            return None

        # 🔥 fuerza
        if cuerpo > rango * 0.75:
            score += 15
        else:
            return None

        # 🔥 ruptura
        if (direccion == "call" and c1 > h2) or (direccion == "put" and c1 < l2):
            score += 15
        else:
            return None

        # 🔥 presión final
        if (direccion == "call" and c1 >= h1 - rango * 0.2) or (direccion == "put" and c1 <= l1 + rango * 0.2):
            score += 10
        else:
            return None

        # 🔥 volatilidad (mejor par)
        vol = np.mean(highs[-20:] - lows[-20:])
        vol_base = np.mean(highs[-50:] - lows[-50:])

        if vol > vol_base:
            score += 10
        else:
            return None

        return direccion, score

    except:
        return None


# ==========================
# 🔥 AGOTAMIENTO (REVERSIÓN)
# ==========================
def evaluar_agotamiento(velas):
    try:
        if len(velas) < 120:
            return None

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)

        rango = h1 - l1
        if rango == 0:
            return None

        cuerpo = abs(c1 - o1)
        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        score = 0

        # 🔥 sobreextensión
        extension = abs(closes[-1] - closes[-30])
        rango_prom = np.mean(highs[-20:] - lows[-20:])

        if extension < rango_prom * 4:
            return None

        score += 20

        # 🔥 desaceleración
        p1 = np.polyfit(range(20), closes[-20:], 1)[0]
        p2 = np.polyfit(range(10), closes[-10:], 1)[0]

        if not ((p2 < p1 and p1 > 0) or (p2 > p1 and p1 < 0)):
            return None

        score += 20

        # 🔥 vela rechazo
        if mecha_sup > cuerpo * 1.5:
            direccion = "put"
            score += 30
        elif mecha_inf > cuerpo * 1.5:
            direccion = "call"
            score += 30
        else:
            return None

        # 🔥 zona extrema
        maximo = max(highs[-20:])
        minimo = min(lows[-20:])

        if abs(c1 - maximo) < rango * 1.5 or abs(c1 - minimo) < rango * 1.5:
            score += 20
        else:
            return None

        return direccion, score

    except:
        return None


# ==========================
# 🎯 SELECCIÓN FINAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 control de frecuencia
    if ahora - ultima_operacion < 7200:
        return None

    # ⏱️ entrada en cierre
    if int(ahora) % 60 < 58:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        cont = evaluar_continuacion(velas)
        rev  = evaluar_agotamiento(velas)

        for resultado in [cont, rev]:
            if resultado:
                direccion, score = resultado

                if score > mejor_score:
                    mejor_score = score
                    mejor = (par, direccion, score)

    # 🔥 SOLO ENTRADAS PERFECTAS
    if mejor and mejor_score >= 90:
        ultima_operacion = ahora
        return mejor

    return None
