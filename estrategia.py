def detectar_entrada_oculta(data):

    mejor = None
    mejor_score = 0

    for par, velas in data.items():

        if len(velas) < 5:
            continue

        # =========================
        # VELAS
        # =========================
        v_impulso = velas[-4]   # vela donde nace la señal
        v_confirm = velas[-3]   # vela de confirmación

        # =========================
        # FUNCIONES
        # =========================
        def cuerpo(v):
            return abs(v["close"] - v["open"])

        def alcista(v):
            return v["close"] > v["open"]

        def bajista(v):
            return v["close"] < v["open"]

        def mecha_sup(v):
            return v["max"] - max(v["open"], v["close"])

        def mecha_inf(v):
            return min(v["open"], v["close"]) - v["min"]

        def limpia(v):
            return (
                cuerpo(v) > 0.00015 and
                mecha_sup(v) < cuerpo(v) * 0.8 and
                mecha_inf(v) < cuerpo(v) * 0.8
            )

        # =========================
        # IMPULSO
        # =========================
        impulso_call = alcista(v_impulso) and cuerpo(v_impulso) > 0.0002
        impulso_put = bajista(v_impulso) and cuerpo(v_impulso) > 0.0002

        # =========================
        # CONFIRMACIÓN
        # =========================
        confirm_call = (
            alcista(v_confirm) and
            v_confirm["close"] > v_impulso["close"] and
            limpia(v_confirm)
        )

        confirm_put = (
            bajista(v_confirm) and
            v_confirm["close"] < v_impulso["close"] and
            limpia(v_confirm)
        )

        # =========================
        # SCORE
        # =========================
        score = 0

        if impulso_call and confirm_call:
            score = 10
            direccion = "call"

        elif impulso_put and confirm_put:
            score = 10
            direccion = "put"

        else:
            continue

        if score > mejor_score:
            mejor_score = score
            mejor = (par, direccion, score)

    return mejor
