import time
import os
import requests
import sys
import threading
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([EMAIL, PASSWORD, TOKEN, CHAT_ID]):
    raise Exception("Faltan variables de entorno")

MONTO = 1200
CUENTA = "PRACTICE"

ultima_entrada = 0
ultimo_par = None
operando = False


# =========================
# TELEGRAM (NO BLOQUEANTE)
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
# CONEXIÓN ROBUSTA
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
            print(f"Error conexión: {e}")

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
# PARES SEGUROS (SIN ERRORES)
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
# VALIDAR ACTIVO ABIERTO
# =========================
def activo_abierto(iq, par):
    try:
        data = iq.get_all_open_time()
        return data["binary"][par]["open"]
    except:
        return False


# =========================
# TIMING PRECISO
# =========================
def esperar_entrada():
    while int(time.time() % 60) < 59:
        time.sleep(0.01)


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
# OPERAR (ESTABLE)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada, operando

    if operando:
        return False

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_abierto(iq, par):
        return False

    operando = True

    esperar_entrada()

    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)

        if status:
            log(f"""🚀 OPERACIÓN

Par: {par}
Dirección: {direccion.upper()}
Monto: ${MONTO}
ID: {order_id}
""")
            ultima_entrada = time.time()
        else:
            print("❌ No ejecutó la orden")

    except Exception as e:
        print(f"Error operación: {e}")

    operando = False
    return True


# =========================
# LOOP PRINCIPAL (ANTI-CRASH)
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

                # evitar repetir mismo par
                if par == ultimo_par:
                    continue

                log(f"""📊 SEÑAL

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
""")

                # confirmación inmediata
                velas_final = obtener_velas(iq, par)

                if not velas_final:
                    continue

                confirmacion = detectar_entrada_oculta({par: velas_final})

                if confirmacion:
                    operar(iq, par, direccion)
                    ultimo_par = par
                else:
                    print("Señal cancelada")

            time.sleep(0.3)

        except Exception as e:
            print(f"Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print(f"Reiniciando bot por error crítico: {e}")
            time.sleep(5)
