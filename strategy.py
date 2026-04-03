import numpy as np

def detectar_entrada(velas):
    try:
        if len(velas) < 20:
            return None

        vela = velas[-1]

        o = float(vela["open"])
        c = float(vela["close"])
        h = float(vela["max"])
        l = float(vela["min"])

        # ==========================
        # 🔥 ANALISIS COMPLETO DE VELA
        # ==========================
        cuerpo = abs(c - o)
        rango = h - l

        if rango == 0:
            return None

        mecha_superior = h - max(o, c)
        mecha_inferior = min(o, c) - l

        fuerza = cuerpo / rango

        # ==========================
        # 📊 PRESIÓN REAL
        # ==========================
        presion_compra = (
            c > o and
            cuerpo > (rango * 0.5) and
            mecha_inferior < cuerpo
        )

        presion_venta = (
            c < o and
            cuerpo > (rango * 0.5) and
            mecha_superior < cuerpo
        )

        # ==========================
        # 🔄 AGOTAMIENTO (RECHAZO)
        # ==========================
        agotamiento_compra = mecha_superior > cuerpo * 1.2
        agotamiento_venta = mecha_inferior > cuerpo * 1.2

        # ==========================
        # 🎯 DECISIÓN FINAL
        # ==========================
        if presion_compra and not agotamiento_compra:
            return "call"

        if presion_venta and not agotamiento_venta:
            return "put"

        # reversión por rechazo
        if agotamiento_compra:
            return "put"

        if agotamiento_venta:
            return "call"

        return None

    except Exception as e:
        print("ERROR estrategia:", e)
        return None
