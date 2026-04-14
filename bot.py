import time
import os
import requests
import sys
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

MONTO = 3
CUENTA = "PRACTICE"

ultima_entrada = 0
ultima_senal = None


# =========================
# LOG + TELEGRAM
# =========================
def log(msg):
    print(msg)
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass


# =========================
# TIEMPO SERVIDOR
# =========================
def tiempo_servidor(iq):
    return int(iq.get_server_timestamp())


# =========================
# ESPERA NUEVA VELA (SYNC REAL)
# =========================
def esperar_cierre_vela(iq):
    while True:
        server_time = tiempo_servidor(iq)
        if server_time % 60 == 0:
            break
        time.sleep(0.05)


# =========================
# ESPERA SEGUNDO 58
# =========================
def esperar_entrada(iq):
    while True:
        server_time = tiempo_servidor(iq)
        if server_time % 60 >= 58:
            break
        time.sleep(0.01)


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
                iq.update_ACTIVES_OPCODE()
                time.sleep(2)

                log("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            log(f"Error conexión: {e}")

        time.sleep(5)


# =========================
# RECONEXIÓN
# =========================
def asegurar_conexion(iq):
    try:
        if not iq.check_connect():
            log("Reconectando...")
            return conectar()

        return iq
    except:
        return conectar()


# =========================
# PARES OTC
# =========================
PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDZAR-OTC",
    "EURJPY-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# OBTENER VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, tiempo_servidor(iq))

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
# VALIDAR DIGITAL OTC
# =========================
def activo_abierto(iq, par):
    try:
        digital, _ = iq.get_digital_underlying_list_data()
        return par in digital
    except:
        return False


# =========================
# FILTRO MERCADO MUERTO
# =========================
def mercado_activo(velas):
    ultima = velas[-1]
    rango = ultima["max"] - ultima["min"]
    return rango > 0.0002


# =========================
# CONFIRMACIÓN FINAL
# =========================
def confirmar_direccion(velas, direccion):
    ultima = velas[-1]

    if ultima["close"] > ultima["open"]:
        confirmacion = "call"
    else:
        confirmacion = "put"

    return confirmacion == direccion


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion, velas):
    global ultima_entrada

    if time.time() - ultima_entrada < 30:
        return False

    if not activo_abierto(iq, par):
        log(f"❌ Activo no disponible: {par}")
        return False

    if not mercado_activo(velas):
        log(f"⚠️ Mercado muerto: {par}")
        return False

    if not confirmar_direccion(velas, direccion):
        log(f"❌ Sin confirmación: {par}")
        return False

    log(f"⏳ Esperando entrada {par}")

    esperar_entrada(iq)

    try:
        iq.subscribe_strike_list(par, 1)
        time.sleep(0.3)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            log(f"""✅ OPERACIÓN EJECUTADA

{par} {direccion.upper()}
Expiración: 1M
""")
            ultima_entrada = time.time()
            return True
        else:
            log("❌ No ejecutó")
            return False

    except Exception as e:
        log(f"❌ Error operación: {e}")
        return False


# =========================
# MAIN
# =========================
def run():
    global ultima_senal

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            # 🔥 ESPERAR CIERRE REAL DE VELA
            esperar_cierre_vela(iq)

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                if velas:
                    data[par] = velas

            if not data:
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                # 🔥 FILTRO DE CALIDAD
                if score < 80:
                    continue

                # 🔥 EVITAR REPETICIÓN
                if señal == ultima_senal:
                    continue

                log(f"""📊 SEÑAL

{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion, data[par])

                ultima_senal = señal

            time.sleep(0.05)

        except Exception as e:
            log(f"❌ Error general: {e}")
            time.sleep(2)


if __name__ == "__main__":
    run()
