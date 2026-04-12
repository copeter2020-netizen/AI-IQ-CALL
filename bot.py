import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta, niveles
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

ultimo_mensaje = ""
ultimo_envio = 0


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(par, direccion, score, tipo="SEÑAL"):
    global ultimo_mensaje, ultimo_envio

    ahora = time.time()

    mensaje = f"""🚀 {tipo}

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}

📊 Score: {score}
"""

    if mensaje == ultimo_mensaje and (ahora - ultimo_envio) < 30:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": mensaje
            },
            timeout=5
        )

        ultimo_mensaje = mensaje
        ultimo_envio = ahora

    except Exception as e:
        print("❌ Error Telegram:", e)


# =========================
# CONEXIÓN
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# DATOS 1 MIN
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# PRECIO ACTUAL
# =========================
def precio_actual(iq, par):
    try:
        velas = iq.get_candles(par, 60, 1, time.time())
        return velas[-1]["close"]
    except:
        return None


# =========================
# ENTRADA INTELIGENTE
# =========================
def esperar_toque_y_operar(iq, par, direccion, score):

    inicio = time.time()
    tiempo_limite = 300  # 5 minutos

    while time.time() - inicio < tiempo_limite:

        velas = obtener_velas(iq, par)
        if not velas:
            continue

        df = pd.DataFrame(velas)
        soporte, resistencia = niveles(df)

        precio = precio_actual(iq, par)

        if precio is None:
            continue

        # 🔥 PUT en resistencia
        if direccion == "put" and precio >= resistencia:
            print(f"🎯 Entrada en RESISTENCIA {par}")
            enviar_mensaje(par, direccion, score, "ENTRADA EN RESISTENCIA")

            status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)
            return status

        # 🔥 CALL en soporte
        if direccion == "call" and precio <= soporte:
            print(f"🎯 Entrada en SOPORTE {par}")
            enviar_mensaje(par, direccion, score, "ENTRADA EN SOPORTE")

            status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)
            return status

        time.sleep(1)

    print("⏱ No tocó zona, no se opera")
    return False


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ Falta estrategia.py")
        return

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            if time.time() - ultima_operacion < 30:
                time.sleep(1)
                continue

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas
                time.sleep(0.2)

            if not data:
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🚨 SEÑAL {par} {direccion} Score:{score}")

                enviar_mensaje(par, direccion, score, "SEÑAL DETECTADA")

                if esperar_toque_y_operar(iq, par, direccion, score):
                    ultima_operacion = time.time()
                    time.sleep(300)

            else:
                time.sleep(1)

        except Exception as e:
            print("❌ Error:", e)
            iq = conectar()


if __name__ == "__main__":
    run()
