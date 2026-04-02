import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 100, time.time())
    except:
        return None

    if not velas or len(velas) < 30:
        return None

    vela_prev = velas[-4]
    vela_trampa = velas[-3]

    # ==========================
    # 🔧 FUNCIONES
    # ==========================
    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_prev) == 0 or rango(vela_trampa) == 0:
        return None

    score = 0

    # ==========================
    # 🔥 1. FUERZA (ANTI DOJI)
    # ==========================
    if cuerpo(vela_prev) > rango(vela_prev) * 0.6:
        score += 1

    if cuerpo(vela_trampa) > rango(vela_trampa) * 0.5:
        score += 1

    # ==========================
    # 🔥 2. ANTI LATERAL
    # ==========================
    zona = velas[-15:]
    rango_total = max(v["max"] for v in zona) - min(v["min"] for v in zona)

    if rango_total > rango(vela_trampa) * 3:
        score += 1

    # ==========================
    # 🔥 3. LIQUIDEZ (SWEEP)
    # ==========================
    maximo = max(v["max"] for v in velas[-30:-3])
    minimo = min(v["min"] for v in velas[-30:-3])

    sweep_alcista = vela_trampa["max"] > maximo
    sweep_bajista = vela_trampa["min"] < minimo

    if sweep_alcista or sweep_bajista:
        score += 1

    # ==========================
    # 🔥 4. IMPULSO PREVIO
    # ==========================
    impulso = velas[-7:-3]

    alcista = all(v["close"] > v["open"] for v in impulso)
    bajista = all(v["close"] < v["open"] for v in impulso)

    if alcista or bajista:
        score += 1

    # ==========================
    # 🔥 5. ESTRUCTURA
    # ==========================
    estructura = velas[-12:-3]

    alc = sum(1 for v in estructura if v["close"] > v["open"])
    baj = sum(1 for v in estructura if v["close"] < v["open"])

    if alc >= 7 or baj >= 7:
        score += 1

    # ==========================
    # 🔥 6. RECHAZO (MECHA)
    # ==========================
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    if mecha_sup > cuerpo(vela_trampa) * 1.5 or mecha_inf > cuerpo(vela_trampa) * 1.5:
        score += 1

    # ==========================
    # 🔥 DECISIÓN FINAL (QUANT)
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
