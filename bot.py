import time
import json
import os
from estrategia import detectar_entrada_oculta

HISTORIAL = "historial.json"

def esperar_apertura():
    while True:
        if int(time.time()) % 60 == 0:
            break
        time.sleep(0.2)

def guardar_trade(par, direccion, resultado, score):
    data = []

    if os.path.exists(HISTORIAL):
        with open(HISTORIAL, "r") as f:
            data = json.load(f)

    data.append({
        "par": par,
        "direccion": direccion,
        "resultado": resultado,
        "score": score
    })

    with open(HISTORIAL, "w") as f:
        json.dump(data, f, indent=4)

def analizar_historial():
    if not os.path.exists(HISTORIAL):
        return 6

    with open(HISTORIAL, "r") as f:
        data = json.load(f)

    if len(data) < 20:
        return 6

    wins = len([d for d in data if d["resultado"] == "win"])
    total = len(data)

    winrate = wins / total

    if winrate < 0.5:
        return 8
    elif winrate > 0.7:
        return 5

    return 6


# ==========================
# SIMULACIÓN (CÁMBIALO POR API REAL)
# ==========================
def obtener_datos():
    return {}  # aquí conectas IQ Option


def ejecutar_trade(par, direccion):
    print(f"📊 Ejecutando {direccion} en {par}")
    return "win"  # simulación


# ==========================
# LOOP PRINCIPAL
# ==========================
def main():
    print("🤖 BOT SNIPER IA INICIADO")

    while True:

        data = obtener_datos()

        entrada = detectar_entrada_oculta(data)

        if entrada:
            par, direccion, score = entrada

            min_score = analizar_historial()

            if score >= min_score:
                print(f"🎯 Señal detectada {par} {direccion} score={score}")

                esperar_apertura()

                resultado = ejecutar_trade(par, direccion)

                guardar_trade(par, direccion, resultado, score)

        time.sleep(1)


if __name__ == "__main__":
    main()
