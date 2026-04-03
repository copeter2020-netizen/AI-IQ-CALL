import time

ultima_operacion = 0

def detectar_entrada(data):
    global ultima_operacion

    try:
        ahora = time.time()

        if ahora - ultima_operacion < 1800:
            return None

        precio = data["price"]
        volumen = data["volume"]
        delta = data["delta"]

        # ==========================
        # 🔥 CONDICIÓN REAL
        # ==========================
        compra_fuerte = volumen > data["vol_prom"] and delta > 0
        venta_fuerte = volumen > data["vol_prom"] and delta < 0

        # ==========================
        # 🔥 CONTINUIDAD
        # ==========================
        tendencia = data["trend"]

        if compra_fuerte and tendencia == "up":
            ultima_operacion = ahora
            return "call"

        if venta_fuerte and tendencia == "down":
            ultima_operacion = ahora
            return "put"

        return None

    except:
        return None
