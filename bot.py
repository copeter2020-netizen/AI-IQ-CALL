import time
from iqoptionapi.stable_api import IQ_Option
from estrategia import detect_signal

EMAIL = "TU_CORREO"
PASSWORD = "TU_PASSWORD"

AMOUNT = 1
EXPIRATION = 5  # minutos


# 🔌 CONECTAR
def conectar():
    while True:
        try:
            print("🔌 Conectando...")
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            # 👇 Forzar sesión (importante en algunos casos)
            try:
                iq.change_balance("PRACTICE")
            except:
                pass

            if iq.check_connect():
                print("✅ Conectado correctamente")
                return iq
            else:
                print("❌ Falló conexión, reintentando...")

        except Exception as e:
            print(f"❌ Error conexión: {e}")

        time.sleep(5)


# 🔄 VERIFICAR CONEXIÓN
def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            print("⚠️ Conexión perdida, reconectando...")
            return conectar()
    except:
        return conectar()

    return iq


# 📊 OBTENER PARES ABIERTOS
def obtener_pares(iq):
    try:
        iq = asegurar_conexion(iq)

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


# 🔍 ANALIZAR PAR
def analizar_par(iq, par):
    try:
        iq = asegurar_conexion(iq)

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


# 🚀 EJECUTAR TRADE
def ejecutar_trade(iq, par, direccion):
    try:
        iq = asegurar_conexion(iq)

        status, trade_id = iq.buy_digital_spot(par, AMOUNT, direccion, EXPIRATION)

        if status:
            print(f"🚀 OPERANDO {par} {direccion.upper()} (${AMOUNT})")
        else:
            print(f"❌ Falló trade en {par}")

        return iq

    except Exception as e:
        print(f"❌ Error ejecutando trade: {e}")
        return iq


# 🚀 INICIO DEL BOT
iq = conectar()

print("🔥 BOT SCANNER ACTIVO (5M)")

while True:
    try:
        iq = asegurar_conexion(iq)

        pares = obtener_pares(iq)

        mejor = None

        for par in pares:
            data = analizar_par(iq, par)

            if data:
                if mejor is None or data["strength"] > mejor["strength"]:
                    mejor = data

        if mejor:
            print(f"🏆 MEJOR PAR: {mejor['par']} | Señal: {mejor['signal']}")
            iq = ejecutar_trade(iq, mejor["par"], mejor["signal"])
        else:
            print("⏳ Sin oportunidades claras...")

        time.sleep(10)

    except Exception as e:
        print(f"❌ Error general: {e}")
        time.sleep(5)
