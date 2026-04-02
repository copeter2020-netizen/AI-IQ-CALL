import time


# ==========================
# 🔥 FILTRO PAYOUT
# ==========================
def payout_valido(iq, par, minimo=70):
    try:
        profit = iq.get_all_profit()
        p = profit.get(par, {})
        digital = p.get("digital", 0)
        return digital >= minimo
    except:
        return False


# ==========================
# 🔥 MULTI ENTRADA CONTROLADA
# ==========================
def multi_entrada(resultado_anterior):
    """
    Martingala inteligente (máximo 2 niveles)
    """
    if resultado_anterior == "loss_1":
        return 2  # segunda entrada
    if resultado_anterior == "loss_2":
        return 3  # tercera entrada
    return 1      # entrada normal


# ==========================
# 🧠 ESTRATEGIA PRINCIPAL
# ==========================
def detectar_trampa(iq, par):

    # ==========================
    # 🔥 FILTRO PAYOUT
    # ==========================
    if not payout_valido(iq, par):
        return None

    try:
        velas = iq.get_candles(par, 60, 100, time.time())
    except:
        return None

    if not velas or len(velas) < 50:
        return None

    vela_base = velas[-5]
    vela_prev = velas[-4]
    vela_trampa = velas[-3]

    # ==========================
    # FUNCIONES
    # ==========================
    def cuerpo(v):
        return abs(v["close"] - v["open"])

    def rango(v):
        return v["max"] - v["min"]

    if rango(vela_trampa) == 0:
        return None

    score = 0

    # ==========================
    # 🔥 1. IMPULSO FUERTE
    # ==========================
    if cuerpo(vela_prev) > rango(vela_prev) * 0.6:
        score += 1

    # ==========================
    # 🔥 2. CONTINUIDAD (OBLIGATORIO)
    # ==========================
    if (
        vela_base["close"] > vela_base["open"] and
        vela_prev["close"] > vela_prev["open"]
    ) or (
        vela_base["close"] < vela_base["open"] and
        vela_prev["close"] < vela_prev["open"]
    ):
        score += 1
    else:
        return None

    # ==========================
    # 🔥 3. TRAMPA INSTITUCIONAL (LIQUIDEZ)
    # ==========================
    maximo = max(v["max"] for v in velas[-50:-3])
    minimo = min(v["min"] for v in velas[-50:-3])

    sweep_alcista = vela_trampa["max"] > maximo
    sweep_bajista = vela_trampa["min"] < minimo

    if sweep_alcista or sweep_bajista:
        score += 2  # peso fuerte
    else:
        return None

    # ==========================
    # 🔥 4. RECHAZO FUERTE (MANIPULACIÓN)
    # ==========================
    mecha_sup = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inf = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    if mecha_sup > cuerpo(vela_trampa) * 1.5 or mecha_inf > cuerpo(vela_trampa) * 1.5:
        score += 1

    # ==========================
    # 🔥 5. ANTI LATERAL
    # ==========================
    zona = velas[-20:]
    rango_total = max(v["max"] for v in zona) - min(v["min"] for v in zona)

    if rango_total > rango(vela_trampa) * 3:
        score += 1

    # ==========================
    # 🔥 6. ESTRUCTURA (DOMINANCIA)
    # ==========================
    estructura = velas[-15:-3]

    alc = sum(1 for v in estructura if v["close"] > v["open"])
    baj = sum(1 for v in estructura if v["close"] < v["open"])

    if alc >= 10 or baj >= 10:
        score += 1

    # ==========================
    # 🔥 FILTRO FINAL (ALTA PRECISIÓN)
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
        return {
            "action": "put",
            "entrada": multi_entrada(None)
        }

    # ==========================
    # 🔺 TRAMPA ABAJO → CALL
    # ==========================
    if (
        sweep_bajista and
        vela_trampa["close"] > vela_trampa["open"] and
        vela_prev["close"] > vela_prev["open"]
    ):
        return {
            "action": "call",
            "entrada": multi_entrada(None)
        }

    return None
