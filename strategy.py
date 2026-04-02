import time


def detectar_trampa(iq, par):

    try:
        velas = iq.get_candles(par, 60, 60, time.time())
    except:
        return None

    if not velas or len(velas) < 15:
        return None

    vela_trampa = velas[-2]
    vela_anterior = velas[-3]

    cuerpo = abs(vela_trampa["close"] - vela_trampa["open"])
    rango = vela_trampa["max"] - vela_trampa["min"]

    if rango == 0:
        return None

    mecha_superior = vela_trampa["max"] - max(vela_trampa["close"], vela_trampa["open"])
    mecha_inferior = min(vela_trampa["close"], vela_trampa["open"]) - vela_trampa["min"]

    ultimas = velas[-10:]
    rango_total = max(v["max"] for v in ultimas) - min(v["min"] for v in ultimas)

    if rango_total < (rango * 3):
        return None

    maximo = max(v["max"] for v in velas[:-2])
    minimo = min(v["min"] for v in velas[:-2])

    trampa_venta = (
        vela_trampa["max"] > maximo and
        vela_trampa["close"] < vela_trampa["open"] and
        mecha_superior > cuerpo * 1.8 and
        cuerpo > (rango * 0.3)
    )

    trampa_compra = (
        vela_trampa["min"] < minimo and
        vela_trampa["close"] > vela_trampa["open"] and
        mecha_inferior > cuerpo * 1.8 and
        cuerpo > (rango * 0.3)
    )

    if trampa_venta and vela_anterior["close"] > vela_anterior["open"]:
        return {"action": "call"}  # invertido

    if trampa_compra and vela_anterior["close"] < vela_anterior["open"]:
        return {"action": "put"}   # invertido

    return None
