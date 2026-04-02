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
    vela_trampa = velas[-2]   # vela actual cerrada (trampa)
    vela_anterior = velas[-3]

    # ==========================
    # 🔥 NIVELES DEL MERCADO
    # ==========================
    maximo = max(v["max"] for v in velas[-10:-2])
    minimo = min(v["min"] for v in velas[-10:-2])

    # ==========================
    # 🔥 TRAMPA ALCISTA (FAKE BREAK ARRIBA)
    # Rompe arriba pero cierra rojo
    # ==========================
    if (
        vela_trampa["max"] > maximo and
        vela_trampa["close"] < vela_trampa["open"]
    ):
        return {"action": "put"}

    # ==========================
    # 🔥 TRAMPA BAJISTA (FAKE BREAK ABAJO)
    # Rompe abajo pero cierra verde
    # ==========================
    if (
        vela_trampa["min"] < minimo and
        vela_trampa["close"] > vela_trampa["open"]
    ):
        return {"action": "call"}

    return None
