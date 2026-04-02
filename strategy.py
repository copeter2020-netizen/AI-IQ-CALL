import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 30, time.time())
    except:
        return None

    if not velas or len(velas) < 10:
        return None

    # ==========================
    # 🔥 DEFINICIÓN DE VELAS
    # ==========================
    vela_prev = velas[-4]     # vela anterior a la trampa (continuación)
    vela_trampa = velas[-3]   # vela de trampa

    # ==========================
    # 🔥 NIVELES DEL MERCADO
    # ==========================
    maximo = max(v["max"] for v in velas[-10:-3])
    minimo = min(v["min"] for v in velas[-10:-3])

    # ==========================
    # 🔥 TRAMPA ALCISTA (FAKE BREAK ARRIBA)
    # ==========================
    if (
        vela_trampa["max"] > maximo and
        vela_trampa["close"] < vela_trampa["open"]
    ):
        # 🔥 CONTINUACIÓN PREVIA BAJISTA
        if vela_prev["close"] < vela_prev["open"]:
            return {"action": "put"}

    # ==========================
    # 🔥 TRAMPA BAJISTA (FAKE BREAK ABAJO)
    # ==========================
    if (
        vela_trampa["min"] < minimo and
        vela_trampa["close"] > vela_trampa["open"]
    ):
        # 🔥 CONTINUACIÓN PREVIA ALCISTA
        if vela_prev["close"] > vela_prev["open"]:
            return {"action": "call"}

    return None
