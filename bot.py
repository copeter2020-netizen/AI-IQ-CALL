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
            print("🔄 Intentando conectar...")
            iq = IQ_Option(EMAIL, PASSWORD)

            status, reason = iq.connect()

            if status:
                print("✅ Conectado correctamente")
                enviar_telegram("✅ Conectado a IQ Option")

                iq.change_balance("PRACTICE")
                return iq

            else:
                print(f"❌ Fallo conexión: {reason}")
                enviar_telegram(f"❌ Fallo conexión: {reason}")
                time.sleep(10)

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(10)


Iq = conectar()


def esperar_cierre_vela():
    while True:
        try:
            t = Iq.get_server_timestamp()
            if int(t) % 60 == 0:
                return True
            time.sleep(0.3)
        except:
            return False


def obtener_candles():
    try:
        return Iq.get_candles(PAR, TIMEFRAME, 100, time.time())
    except:
        return None


while True:
    try:

        if not Iq.check_connect():
            print("🔌 Conexión perdida")
            enviar_telegram("🔌 Reconectando...")
            Iq = conectar()
            continue

        if not esperar_cierre_vela():
            continue

        candles = obtener_candles()

        if not candles:
            print("❌ Error velas")
            continue

        señal = detectar_entrada(candles)

        if señal:
            direccion, expiracion = señal

            print(f"📊 {direccion}")
            enviar_telegram(f"📊 {direccion}")

            status, trade_id = Iq.buy(MONTO, PAR, direccion, expiracion)

            if status:
                print("🔥 EJECUTADA")
                enviar_telegram("🔥 OPERACIÓN EJECUTADA")
            else:
                print("❌ Fallo operación")
                enviar_telegram("❌ Fallo operación")

        else:
            print("⏳ Sin señal")

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR:", e)
        enviar_telegram(f"⚠️ ERROR: {e}")
        time.sleep(5)
