import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 50, time.time())
    except:
        return None

    if not velas or len(velas) < 10:
        return None

    vela = velas[-2]

    cuerpo = abs(vela["close"] - vela["open"])
    rango = vela["max"] - vela["min"]

    if rango == 0:
        return None

    mecha_sup = vela["max"] - max(vela["close"], vela["open"])
    mecha_inf = min(vela["close"], vela["open"]) - vela["min"]

    maximo = max(v["max"] for v in velas[:-2])
    minimo = min(v["min"] for v in velas[:-2])

    # 🔥 TRAMPA VENTA (invertido → CALL)
    if (
        vela["max"] > maximo and
        vela["close"] < vela["open"] and
        mecha_sup > cuerpo * 1.5
    ):
        return {"action": "call"}

    # 🔥 TRAMPA COMPRA (invertido → PUT)
    if (
        vela["min"] < minimo and
        vela["close"] > vela["open"] and
        mecha_inf > cuerpo * 1.5
    ):
        return {"action": "put"}

    return None
