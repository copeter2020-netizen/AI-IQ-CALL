import time


def detectar_trampa(iq, par):

    velas = iq.get_candles(par, 60, 20, time.time())

    if not velas or len(velas) < 3:
        return None

    c1 = velas[-1]  # vela actual
    c2 = velas[-2]  # 🔥 vela anterior (MANDA TODO)

    max_prev = max(v["max"] for v in velas[:-1])
    min_prev = min(v["min"] for v in velas[:-1])

    # ==========================
    # 🔥 SOLO VALIDACIÓN DE TRAMPA
    # ==========================
    hay_trampa = (
        (c1["max"] > max_prev and c1["close"] < c1["open"]) or
        (c1["min"] < min_prev and c1["close"] > c1["open"])
    )

    if not hay_trampa:
        return None

    # ==========================
    # 🔒 CONTINUIDAD FORZADA
    # ==========================

    # 🟢 VERDE → CALL
    if c2["close"] > c2["open"]:
        return {"action": "call"}

    # 🔴 ROJA → PUT
    if c2["close"] < c2["open"]:
        return {"action": "put"}

    # ❌ DOJI → BLOQUEADO
    return None
