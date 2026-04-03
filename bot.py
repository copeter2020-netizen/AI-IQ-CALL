import time
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

PAR = "EURUSD-OTC"
MONTO = 2
TIMEFRAME = 60  # 1 minuto

Iq = IQ_Option(EMAIL, PASSWORD)
Iq.connect()

if not Iq.check_connect():
    print("❌ Error conectando")
    exit()

print("✅ BOT ACTIVADO")

Iq.change_balance("PRACTICE")


def esperar_cierre_vela():
    while True:
        server_time = Iq.get_server_timestamp()
        segundos = int(server_time) % 60

        # Espera justo cierre de vela
        if segundos == 0:
            break

        time.sleep(0.5)


def obtener_candles():
    return Iq.get_candles(PAR, TIMEFRAME, 100, time.time())


while True:
    try:
        esperar_cierre_vela()

        candles = obtener_candles()

        señal = detectar_entrada(candles)

        if señal:
            direccion, expiracion = señal

            print(f"📊 SEÑAL: {direccion}")

            status, id = Iq.buy(MONTO, PAR, direccion, expiracion)

            if status:
                print(f"🔥 ENTRADA EJECUTADA: {direccion}")
            else:
                print("❌ Error al ejecutar")

        else:
            print("⏳ Sin señal")

        time.sleep(1)

    except Exception as e:
        print("⚠️ ERROR:", e)
        time.sleep(5)
