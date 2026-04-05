import time
import random
from estrategia import detectar_entrada_oculta
from telegram_bot import enviar, escuchar

print("✅ BOT CONECTADO")

# ==========================
# SIMULACIÓN DE DATOS (IQ OPTION)
# ==========================
def obtener_datos():

    # ⚠️ AQUÍ luego conectamos IQ Option real
    pares = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

    data = {}

    for par in pares:
        velas = []
        precio = random.uniform(1, 2)

        for _ in range(60):
            open_p = precio
            close_p = precio + random.uniform(-0.001, 0.001)
            high = max(open_p, close_p) + random.uniform(0, 0.0005)
            low = min(open_p, close_p) - random.uniform(0, 0.0005)

            velas.append({
                "open": open_p,
                "close": close_p,
                "max": high,
                "min": low
            })

            precio = close_p

        data[par] = velas

    return data


# ==========================
# LOOP PRINCIPAL
# ==========================
while True:

    activo = escuchar()

    if not activo:
        time.sleep(2)
        continue

    try:
        data = obtener_datos()

        entrada = detectar_entrada_oculta(data)

        if entrada:
            par, direccion, score = entrada

            mensaje = f"📊 ENTRADA\n{par}\n{direccion.upper()}\nScore: {score}"

            print(f"Entrada: {par} {direccion} ⭐{score}")
            enviar(mensaje)

            time.sleep(60)  # evita spam

        else:
            time.sleep(2)

    except Exception as e:
        print("Error:", e)
        time.sleep(5)
