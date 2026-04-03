import time
import numpy as np

ultima_operacion = 0


# ==========================
# 🔥 MERCADO ACTIVO
# ==========================
def mercado_activo(velas):
    try:
        highs = np.array([float(v["max"]) for v in velas])
        lows  = np.array([float(v["min"]) for v in velas])

        vol_actual = np.mean(highs[-5:] - lows[-5:])
        vol_pasada = np.mean(highs[-30:] - lows[-30:])

        if vol_actual < vol_pasada * 0.9:
            return False

        return True
    except:
        return False


# ==========================
# 🔥 ESTRATEGIA AGOTAMIENTO
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    # 🔒 ULTRA SELECTIVO
    if ahora - ultima_operacion < 300:
        return None

    mejor = None
    mejor_score = 0

    for par, velas in data_por_par.items():

        if par not in ["EURUSD", "EURJPY", "EURGBP", "GBPUSD", "USDCHF"]:
            continue

        if len(velas) < 60:
            continue

        if not mercado_activo(velas):
            continue

        closes = np.array([float(v["close"]) for v in velas])
        highs  = np.array([float(v["max"]) for v in velas])
        lows   = np.array([float(v["min"]) for v in velas])

        v1 = velas[-1]
        v2 = velas[-2]
        v3 = velas[-3]

        def d(v):
            return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

        o1,c1,h1,l1 = d(v1)

        rango = h1 - l1
        if rango == 0:
            continue

        cuerpo = abs(c1 - o1)

        mecha_sup = h1 - max(o1, c1)
        mecha_inf = min(o1, c1) - l1

        score = 0

        # ==========================
        # 🔥 1. TENDENCIA PREVIA
        # ==========================
        pendiente = np.polyfit(range(10), closes[-10:], 1)[0]

        if pendiente > 0:
            posible = "put"  # agotamiento arriba
        elif pendiente < 0:
            posible = "call"  # agotamiento abajo
        else:
            continue

        score += 20

        # ==========================
        # 🔥 2. EXTREMO DE PRECIO
        # ==========================
        maximo = max(highs[-20:])
        minimo = min(lows[-20:])

        posicion = (c1 - minimo) / (maximo - minimo)

        if posible == "put" and posicion < 0.85:
            continue

        if posible == "call" and posicion > 0.15:
            continue

        score += 20

        # ==========================
        # 🔥 3. VELA DE RECHAZO (CLAVE)
        # ==========================
        if posible == "put":
            if mecha_sup < cuerpo * 1.5:
                continue
        else:
            if mecha_inf < cuerpo * 1.5:
                continue

        score += 25

        # ==========================
        # 🔥 4. CUERPO DÉBIL
        # ==========================
        if cuerpo > rango * 0.5:
            continue

        score += 15

        # ==========================
        # 🔥 5. PÉRDIDA DE FUERZA
        # ==========================
        p_corto = np.polyfit(range(5), closes[-5:], 1)[0]

        if posible == "put" and p_corto > 0:
            score += 10
        elif posible == "call" and p_corto < 0:
            score += 10
        else:
            continue

        # ==========================
        # 🔥 SELECCIÓN
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, posible, score)

    if mejor and mejor_score >= 70:
        ultima_operacion = ahora
        return mejor

    return None
