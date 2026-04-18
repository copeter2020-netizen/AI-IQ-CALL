import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 560
CUENTA = "PRACTICE"

ultima_entrada = 0


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=5
        )
    except:
        pass


def log(msg):
    print(msg, flush=True)
    enviar_telegram(msg)


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

                # 🔥 evita error 'underlying'
                try:
                    iq.api.digital_option = None
                except:
                    pass

                log("✅ BOT CONECTADO")
                return iq
        except:
            pass

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            return conectar()
        return iq
    except:
        return conectar()


# =========================
# PARES
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDZAR-OTC",
    "USDCHF-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDZAR-OTC"
]


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# TIEMPO
# =========================
def esperar_cierre_vela():
    while int(time.time() % 60) != 59:
        time.sleep(0.05)


def esperar_inicio_vela():
    while int(time.time() % 60) != 0:
        time.sleep(0.001)


# =========================
# OPERAR + RESULTADO
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 60:
        return

    for _ in range(3):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN EJECUTADA

📊 {par}
📈 {direccion.upper()}
💰 {MONTO}
🆔 {order_id}
""")

                ultima_entrada = time.time()

                # 🔥 ESPERAR RESULTADO
                resultado = None

                while resultado is None:
                    try:
                        resultado = iq.check_win_v4(order_id)
                    except:
                        pass

                    time.sleep(1)

                # 🔥 RESULTADO FINAL
                if resultado > 0:
                    log(f"✅ RESULTADO: WIN (+{resultado})")

                elif resultado < 0:
                    log(f"❌ RESULTADO: LOSS ({resultado})")

                else:
                    log("⚪ RESULTADO: EMPATE")

                return

        except Exception as e:
            log(f"Error ejecución: {e}")

        time.sleep(1)

    log("❌ Falló ejecución")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            # 🔥 detectar señal al cierre
            esperar_cierre_vela()

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            señal = detectar_entrada_oculta(data)

            if not señal:
                continue

            par, direccion, score = señal

            enviar_telegram(f"""📢 SEÑAL DETECTADA

📊 Par: {par}
📈 Dirección: {direccion.upper()}
⭐ Score: {score}

⏳ Esperando confirmación...
""")

            # 🔥 esperar confirmación (1 vela)
            esperar_cierre_vela()

            enviar_telegram("🕯 Vela de confirmación completada")

            # 🔥 entrar en nueva vela
            esperar_inicio_vela()

            enviar_telegram("🎯 ENTRANDO AL MERCADO...")

            operar(iq, par, direccion)

        except Exception as e:
            log(f"Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
