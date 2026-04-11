import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

try:
    from estrategia import detectar_entrada_oculta
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 10000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

# 🔥 CONTROL ANTI-SPAM
ultimo_mensaje = ""
ultimo_envio = 0


# =========================
# ⏱ TIMING EXACTO
# =========================
def esperar_cierre_vela():
    while True:
        ahora = time.time()
        restante = 60 - (ahora % 60)

        if restante <= 0.3:
            break

        time.sleep(0.05)


def esperar_cierre_siguiente():
    # esperar cierre actual
    esperar_cierre_vela()

    # esperar una vela completa
    time.sleep(60)

    # esperar cierre exacto de la siguiente
    esperar_cierre_vela()


# =========================
# TELEGRAM MEJORADO
# =========================
def enviar_mensaje(par, direccion, score):
    global ultimo_mensaje, ultimo_envio

    ahora = time.time()

    mensaje = f"""🚀 NUEVA ENTRADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}

📊 Score: {score}
"""

    if mensaje == ultimo_mensaje and (ahora - ultimo_envio) < 60:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": mensaje
            },
            timeout=5
        )

        ultimo_mensaje = mensaje
        ultimo_envio = ahora

    except Exception as e:
        print("❌ Error Telegram:", e)


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
                iq.api.digital_option = None
                print("✅ CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

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
# VALIDAR PAR
# =========================
def par_valido(iq, par):
    try:
        velas = iq.get_candles(par, 60, 1, time.time())
        return velas is not None and len(velas) > 0
    except:
        return False


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion, score):

    if not par_valido(iq, par):
        return False

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")

            enviar_mensaje(par, direccion, score)

            return True

    except Exception as e:
        print("Error operar:", e)

    return False


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ Falta estrategia.py")
        return

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            if time.time() - ultima_operacion < 30:
                time.sleep(0.5)
                continue

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if velas:
                    data[par] = velas

                time.sleep(0.3)

            if not data:
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                # 🔥 ESPERA LA SIGUIENTE VELA Y ENTRA EN SU CIERRE
                esperar_cierre_siguiente()

                if operar(iq, par, direccion, score):
                    ultima_operacion = time.time()
                    time.sleep(60)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("❌ Error general:", e)
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
