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

        if vol_actual < vol_pasada * 0.85:
            return False

        return True
    except:
        return False


# ==========================
# 🔥 ESTRATEGIA PRO FINAL
# ==========================
def detectar_mejor_entrada(data_por_par):
    global ultima_operacion

    ahora = time.time()

    if ahora - ultima_operacion < 180:
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
        o2,c2,h2,l2 = d(v2)

        rango1 = h1 - l1
        rango2 = h2 - l2

        if rango1 == 0 or rango2 == 0:
            continue

        cuerpo1 = abs(c1 - o1)
        cuerpo2 = abs(c2 - o2)

        mecha_sup1 = h1 - max(o1, c1)
        mecha_inf1 = min(o1, c1) - l1

        # ==========================
        # 🔥 1. TENDENCIA
        # ==========================
        pendiente = np.polyfit(range(10), closes[-10:], 1)[0]

        if pendiente > 0:
            direccion = "call"
        elif pendiente < 0:
            direccion = "put"
        else:
            continue

        score = 20

        # ==========================
        # 🔥 2. CONTINUIDAD REAL
        # ==========================
        if direccion == "call":
            if not (c1 > c2 > v3["close"]):
                continue
        else:
            if not (c1 < c2 < v3["close"]):
                continue

        score += 20

        # ==========================
        # 🔥 3. VELAS FUERTES
        # ==========================
        if cuerpo1 < rango1 * 0.6 or cuerpo2 < rango2 * 0.6:
            continue

        score += 15

        # ==========================
        # 🔥 4. SIN RECHAZO
        # ==========================
        if direccion == "call" and mecha_sup1 > cuerpo1 * 0.4:
            continue
        if direccion == "put" and mecha_inf1 > cuerpo1 * 0.4:
            continue

        score += 10

        # ==========================
        # 🔥 5. EVITAR TRAMPA (CLAVE)
        # ==========================
        maximo = max(highs[-20:])
        minimo = min(lows[-20:])

        posicion = (c1 - minimo) / (maximo - minimo)

        # ❌ evitar comprar arriba del todo
        if direccion == "call" and posicion > 0.85:
            continue

        # ❌ evitar vender abajo del todo
        if direccion == "put" and posicion < 0.15:
            continue

        score += 20

        # ==========================
        # 🔥 6. ESPACIO LIBRE
        # ==========================
        if direccion == "call":
            if (maximo - c1) < rango1 * 0.5:
                continue
        else:
            if (c1 - minimo) < rango1 * 0.5:
                continue

        score += 15

        # ==========================
        # 🔥 SELECCIÓN FINAL
        # ==========================
        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    if mejor and mejor_score >= 85:
        ultima_operacion = ahora
        return mejor

    return None
