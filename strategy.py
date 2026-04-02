import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 50, time.time())

    if not velas or len(velas) < 10:
        return None

    vela_trampa = velas[-2]
    vela_anterior = velas[-3]

    cuerpo = abs(vela_trampa["close"] - vela_trampa["open"])
    rango = vela_trampa["max"] - vela_trampa["min"]

    if rango == 0:
        return None

    mecha_superior = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inferior = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    maximo = max(v["max"] for v in velas[:-2])
    minimo = min(v["min"] for v in velas[:-2])

    # 🔴 TRAMPA VENTA
    trampa_venta = (
        vela_trampa["max"] > maximo and
        vela_trampa["close"] < vela_trampa["open"] and
        mecha_superior > cuerpo * 1.5
    )

    # 🟢 TRAMPA COMPRA
    trampa_compra = (
        vela_trampa["min"] < minimo and
        vela_trampa["close"] > vela_trampa["open"] and
        mecha_inferior > cuerpo * 1.5
    )

    confirmacion_put = (
        trampa_venta and
        vela_anterior["close"] > vela_anterior["open"]
    )

    confirmacion_call = (
        trampa_compra and
        vela_anterior["close"] < vela_anterior["open"]
    )

    # 😈 INVERTIDO PRO
    if confirmacion_put:
        return {"action": "call"}

    if confirmacion_call:
        return {"action": "put"}

    return None
