import time
from iqoptionapi.stable_api import IQ_Option
from estrategia import detect_signal

EMAIL = "TU_CORREO"
PASSWORD = "TU_PASSWORD"

AMOUNT = 1
EXPIRATION = 5  # minutos

iq = IQ_Option(EMAIL, PASSWORD)
iq.connect()

if not iq.check_connect():
    print("❌ Error conectando")
    exit()

print("✅ Conectado correctamente")


def obtener_pares():
    try:
        activos = iq.get_all_ACTIVES_OPCODE()
        abiertos = iq.get_all_open_time()

        pares = []

        for par in activos:
            try:
                if abiertos["digital"][par]["open"]:
                    pares.append(par)
            except:
                continue

        return pares

    except Exception as e:
        print(f"❌ Error obteniendo pares: {e}")
        return []


def analizar_par(par):
    try:
        candles = iq.get_candles(par, 60, 50, time.time())

        if not candles:
            return None

        señal = detect_signal(candles)

        if señal:
            print(f"📊 {par} | Señal: {señal['signal']} | Fuerza: {señal['strength']:.2f}")
            return {
                "par": par,
                "signal": señal["signal"],
                "strength": señal["strength"]
            }

        return None

    except Exception as e:
        print(f"❌ Error analizando {par}: {e}")
        return None


def ejecutar_trade(par, direccion):
    try:
        status, id = iq.buy_digital_spot(par, AMOUNT, direccion, EXPIRATION)

        if status:
            print(f"🚀 OPERANDO {par} {direccion.upper()} (${AMOUNT})")
        else:
            print(f"❌ Falló trade en {par}")

    except Exception as e:
        print(f"❌ Error ejecutando trade: {e}")


print("🔥 BOT SCANNER ACTIVO (5M)")

while True:
    try:
        pares = obtener_pares()

        mejor = None

        for par in pares:
            data = analizar_par(par)

            if data:
                if mejor is None or data["strength"] > mejor["strength"]:
                    mejor = data

        if mejor:
            print(f"🏆 MEJOR PAR: {mejor['par']} | Señal: {mejor['signal']}")
            ejecutar_trade(mejor["par"], mejor["signal"])
        else:
            print("⏳ Sin oportunidades claras...")

        time.sleep(10)

    except Exception as e:
        print(f"❌ Error general: {e}")
        time.sleep(5)
