import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

PAR = "EURUSD-OTC"
MONTO = 2
TIMEFRAME = 60

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"


def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        pass


Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando")
    enviar_telegram("❌ Error conectando a IQ Option")
    exit()

print("✅ BOT ACTIVADO")
enviar_telegram("✅ BOT ACTIVADO")

Iq.change_balance("PRACTICE")


def esperar_cierre_vela():
    while True:
        server_time = Iq.get_server_timestamp()
        if int(server_time) % 60 == 0:
            break
        time.sleep(0.3)


def obtener_candles():
    return Iq.get_candles(PAR, TIMEFRAME, 100, time.time())


while True:
    try:
        esperar_cierre_vela()

        candles = obtener_candles()

        # ✅ AQUÍ ESTÁ EL FIX (solo 1 argumento)
        señal = detectar_entrada(candles)

        if señal:
            direccion, expiracion = señal

            print(f"📊 SEÑAL: {direccion}")
            enviar_telegram(f"📊 SEÑAL: {direccion}")

            status, id = Iq.buy(MONTO, PAR, direccion, expiracion)

            if status:
                print("🔥 OPERACIÓN EJECUTADA")
                enviar_telegram("🔥 OPERACIÓN EJECUTADA")
            else:
                print("❌ Error al ejecutar")
                enviar_telegram("❌ Error al ejecutar")

        else:
            print("⏳ Sin señal")

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR:", e)
        enviar_telegram(f"⚠️ ERROR: {e}")
        time.sleep(5)
