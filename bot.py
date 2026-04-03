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


def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ Conectado a IQ Option")
                enviar_telegram("✅ Conectado a IQ Option")
                iq.change_balance("PRACTICE")
                return iq
            else:
                print("❌ Error conectando, reintentando...")
                time.sleep(5)

        except Exception as e:
            print("⚠️ Error conexión:", e)
            time.sleep(5)


Iq = conectar()


def esperar_cierre_vela():
    while True:
        try:
            server_time = Iq.get_server_timestamp()
            if int(server_time) % 60 == 0:
                break
            time.sleep(0.3)
        except:
            return False
    return True


def obtener_candles():
    try:
        return Iq.get_candles(PAR, TIMEFRAME, 100, time.time())
    except:
        return None


while True:
    try:

        if not Iq.check_connect():
            print("🔄 Reconectando...")
            enviar_telegram("🔄 Reconectando...")
            Iq = conectar()
            continue

        if not esperar_cierre_vela():
            continue

        candles = obtener_candles()

        if not candles:
            print("❌ Error obteniendo velas")
            continue

        señal = detectar_entrada(candles)

        if señal:
            direccion, expiracion = señal

            msg = f"📊 SEÑAL: {direccion}"
            print(msg)
            enviar_telegram(msg)

            status, trade_id = Iq.buy(MONTO, PAR, direccion, expiracion)

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
