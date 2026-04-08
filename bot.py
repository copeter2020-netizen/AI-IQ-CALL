import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option

from estrategia import detectar_mejor_entrada

# =========================
# CONFIGURACIÓN
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 13000
TIEMPO_EXPIRACION = 3

PARES = [
    "EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC",
    "EURGBP-OTC", "EURJPY-OTC", "GBPJPY-OTC", "USDCHF-OTC", "USDCAD-OTC"
]

# =========================
# TELEGRAM CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")

def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje
        }
        requests.post(url, data=data, timeout=5)
    except:
        pass  # evita spam de errores

# =========================
# CONEXIÓN
# =========================
def conectar():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    if iq.check_connect():
        msg = "✅ BOT CONECTADO"
        print(msg)
        enviar_telegram(msg)
        return iq
    else:
        print("❌ Error de conexión")
        return None

# =========================
# OBTENER VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

        if not velas:
            return None

        import pandas as pd
        df = pd.DataFrame(velas)

        return df

    except:
        return None

# =========================
# EJECUTAR OPERACIÓN
# =========================
def ejecutar_operacion(iq, par, direccion):
    try:
        accion = "call" if direccion == "call" else "put"

        status, _ = iq.buy(MONTO, par, accion, TIEMPO_EXPIRACION)

        if status:
            msg = f"🚀 ENTRADA\nPar: {par}\nDirección: {accion.upper()}"
            print(msg)
            enviar_telegram(msg)
        else:
            enviar_telegram("❌ Error al ejecutar operación")

    except Exception as e:
        enviar_telegram(f"❌ Error operación: {e}")

# =========================
# LOOP PRINCIPAL
# =========================
def main():
    iq = conectar()
    if not iq:
        return

    operando = False

    while True:
        try:
            if not operando:

                def get_velas(par):
                    return obtener_velas(iq, par)

                mejor = detectar_mejor_entrada(PARES, get_velas)

                if mejor:
                    msg = f"📊 Señal detectada\nPar: {mejor['par']}\nDirección: {mejor['direccion'].upper()}\nScore: {mejor['score']}"
                    print(msg)
                    enviar_telegram(msg)

                    ejecutar_operacion(iq, mejor["par"], mejor["direccion"])
                    operando = True

            time.sleep(TIEMPO_EXPIRACION * 60)
            operando = False

        except Exception as e:
            enviar_telegram(f"❌ Error loop: {e}")
            time.sleep(5)

# =========================
# INICIO
# =========================
if __name__ == "__main__":
    main()
