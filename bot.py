import time
import os
import requests
import sys
import threading
import traceback
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 6500
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None
operando = False


# =========================
# IGNORAR ERROR UNDERLYING
# =========================
def ignorar_errores_hilos():
    def custom_hook(args):
        if "underlying" in str(args.exc_value):
            return
        print("Thread error:", args.exc_value)

    threading.excepthook = custom_hook

ignorar_errores_hilos()


# =========================
# TELEGRAM
# =========================
def enviar_telegram(msg):
    def enviar():
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg},
                timeout=5
            )
        except:
            pass

    threading.Thread(target=enviar, daemon=True).start()


def log(msg):
    print(msg)
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
                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            print("Reconectando...")
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
    "USDJPY-OTC",
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

        if not velas:
            return None

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return None


# =========================
# 🚀 OPERAR INMEDIATO (FIX REAL)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, operando

    if operando:
        return False

    # 🔥 bajar restricción
    if time.time() - ultima_entrada < 10:
        return False

    operando = True

    log(f"⚡ Intentando operar {par} {direccion}")

    # 🔥 REINTENTO REAL
    for intento in range(5):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                log(f"""🚀 OPERACIÓN EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Monto: ${MONTO}
ID: {order_id}
""")
                ultima_entrada = time.time()
                operando = False
                return True
            else:
                print(f"Intento {intento+1}: no ejecutó")

        except Exception as e:
            print(f"Error intento {intento+1}: {e}")

        time.sleep(1)

    log("❌ NO SE PUDO EJECUTAR")
    operando = False
    return False


# =========================
# MAIN
# =========================
def run():
    global ultimo_par

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                if par == ultimo_par:
                    continue

                log(f"""📈 SEÑAL

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
""")

                # 🔥 EJECUCIÓN DIRECTA (SIN FILTROS QUE BLOQUEAN)
                ejecutar = operar(iq, par, direccion)

                if ejecutar:
                    ultimo_par = par

            time.sleep(0.2)

        except Exception as e:
            print("Error general:", e)
            traceback.print_exc()
            time.sleep(2)


# =========================
# ANTI-CRASH
# =========================
if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print("Reiniciando:", e)
            time.sleep(5)
