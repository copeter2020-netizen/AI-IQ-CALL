import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 100, time.time())
    except:
        return None

    if not velas or len(velas) < 40:
        return None

    vela_prev = velas[-4]
    vela_trampa = velas[-3]

    # ==========================
    # FUNCIONES
    # ==========================
    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_prev) == 0 or rango(vela_trampa) == 0:
        return None

    score = 0

    # ==========================
    # 🔥 1. FUERZA VELAS
    # ==========================
    if cuerpo(vela_prev) > rango(vela_prev) * 0.6:
        score += 1

    if cuerpo(vela_trampa) > rango(vela_trampa) * 0.5:
        score += 1

    # ==========================
    # 🔥 2. CONTINUACIÓN REAL
    # ==========================
    if (
        vela_prev["close"] > vela_prev["open"] and
        velas[-5]["close"] > velas[-5]["open"]
    ) or (
        vela_prev["close"] < vela_prev["open"] and
        velas[-5]["close"] < velas[-5]["open"]
    ):
        score += 1
    else:
        return None  # 🔴 obligatorio

    # ==========================
    # 🔥 3. ANTI LATERAL
    # ==========================
    zona = velas[-20:]
    rango_total = max(v["max"] for v in zona) - min(v["min"] for v in zona)

    if rango_total > rango(vela_trampa) * 3:
        score += 1

    # ==========================
    # 🔥 4. LIQUIDEZ (SWEEP)
    # ==========================
    maximo = max(v["max"] for v in velas[-40:-3])
    minimo = min(v["min"] for v in velas[-40:-3])

    sweep_alcista = vela_trampa["max"] > maximo
    sweep_bajista = vela_trampa["min"] < minimo

    if sweep_alcista or sweep_bajista:
        score += 1
    else:
        return None  # 🔴 obligatorio

    # ==========================
    # 🔥 5. IMPULSO PREVIO
    # ==========================
    impulso = velas[-8:-3]

    alcista = all(v["close"] > v["open"] for v in impulso)
    bajista = all(v["close"] < v["open"] for v in impulso)

    if alcista or bajista:
        score += 1

    # ==========================
    # 🔥 6. ESTRUCTURA
    # ==========================
    estructura = velas[-15:-3]

    alc = sum(1 for v in estructura if v["close"] > v["open"])
    baj = sum(1 for v in estructura if v["close"] < v["open"])

    if alc >= 9 or baj >= 9:
        score += 1

    # ==========================
    # 🔥 7. RECHAZO FUERTE
    # ==========================
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    if mecha_sup > cuerpo(vela_trampa) * 1.5 or mecha_inf > cuerpo(vela_trampa) * 1.5:
        score += 1

    # ==========================
    # 🔥 FILTRO FINAL
    # ==========================
    if score < 6:
        return None

    # ==========================
    # 🔻 TRAMPA ARRIBA → PUT
    # ==========================
    if (
        sweep_alcista and
        vela_trampa["close"] < vela_trampa["open"] and
        vela_prev["close"] < vela_prev["open"]
    ):
        return {"action": "put"}

    # ==========================
    # 🔺 TRAMPA ABAJO → CALL
    # ==========================
    if (
        sweep_bajista and
        vela_trampa["close"] > vela_trampa["open"] and
        vela_prev["close"] > vela_prev["open"]
    ):
        return {"action": "call"}

    return None
