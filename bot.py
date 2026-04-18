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
            data={"chat_id": CHAT_ID, "text": msg},
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
    "GBPJPY-OTC"
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
# OPERAR
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

{par} {direccion.upper()}
ID: {order_id}
""")
                ultima_entrada = time.time()
                return
        except:
            pass

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

            log(f"""
📊 SEÑAL DETECTADA

{par} {direccion}
Score: {score}

⏳ Esperando vela de confirmación...
""")

            # 🔥 esperar confirmación (1 vela)
            esperar_cierre_vela()

            log("🕯 Vela de confirmación completada")

            # 🔥 entrar en siguiente vela
            log("🎯 Ejecutando en nueva vela")

            esperar_inicio_vela()

            operar(iq, par, direccion)

        except Exception as e:
            log(f"Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
