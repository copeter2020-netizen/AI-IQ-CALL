import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

# ==============================
# CONFIGURACIÓN
# ==============================

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

PAR = "EURUSD-OTC"
MONTO = 2
TIMEFRAME = 60

# TELEGRAM
TOKEN = "TU_TOKEN_TELEGRAM"
CHAT_ID = "TU_CHAT_ID"

# ==============================
# TELEGRAM
# ==============================

def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mensaje}
        requests.post(url, data=data, timeout=5)
    except:
        pass

# ==============================
# CONEXIÓN IQ OPTION
# ==============================

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando")
    enviar_telegram("❌ Error conectando a IQ Option")
    exit()

print("✅ BOT ACTIVADO")
enviar_telegram("✅ Bot conectado a IQ Option")

Iq.change_balance("PRACTICE")

# ==============================
# FUNCIONES
# ==============================

def esperar_cierre_vela():
    while True:
        server_time = Iq.get_server_timestamp()
        segundos = int(server_time) % 60

        if segundos == 0:
            break

        time.sleep(0.5)


def obtener_candles():
    return Iq.get_candles(PAR, TIMEFRAME, 100, time.time())


# ==============================
# LOOP PRINCIPAL
# ==============================

while True:
    try:
        esperar_cierre_vela()

        candles = obtener_candles()

        señal = detectar_entrada(candles)

        if señal:
            direccion, expiracion = señal

            mensaje = f"📊 SEÑAL: {direccion.upper()} {PAR}"
            print(mensaje)
            enviar_telegram(mensaje)

            status, trade_id = Iq.buy(MONTO, PAR, direccion, expiracion)

            if status:
                msg = f"🔥 OPERACIÓN EJECUTADA: {direccion.upper()}"
                print(msg)
                enviar_telegram(msg)
            else:
                print("❌ Error al ejecutar")
                enviar_telegram("❌ Error al ejecutar operación")

        else:
            print("⏳ Sin señal")

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR:", e)
        enviar_telegram(f"⚠️ ERROR: {e}")
        time.sleep(5)
