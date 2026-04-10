import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# =========================
# IMPORT ESTRATEGIA
# =========================
try:
    from estrategia import detectar_entrada_oculta
except Exception as e:
    print("❌ Error importando estrategia:", e)
    detectar_entrada_oculta = None


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 5000
CUENTA = "PRACTICE"


# =========================
# OBTENER PARES OTC ABIERTOS (FIX UNDERLYING)
# =========================
def obtener_pares_otc(iq):
    try:
        activos = iq.get_all_open_time()
        abiertos = []

        for par, info in activos["digital"].items():
            if "-OTC" in par and info["open"]:
                abiertos.append(par)

        return abiertos

    except Exception as e:
        print("Error obteniendo pares OTC:", e)
        return []


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
    except:
        pass


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
                print("✅ CONECTADO A IQ OPTION")
                enviar_mensaje("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# OBTENER VELAS (ESTABLE)
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 180, time.time())

        if not velas:
            return []

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print(f"Error velas {par}:", e)
        return []


# =========================
# OPERAR SEGURO (FIX UNDERLYING)
# =========================
def operar(iq, par, direccion):

    try:
        # 🔥 VALIDAR DISPONIBILIDAD REAL
        activos = iq.get_all_open_time()

        if par not in activos["digital"]:
            return False

        if not activos["digital"][par]["open"]:
            return False

        # 🔥 OPERACIÓN DIGITAL CORRECTA
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}

📊 Estrategia activa
""")

            return True

    except Exception as e:
        print("Error operar:", e)

    return False


# =========================
# MAIN ROBUSTO
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ No hay estrategia")
        return

    iq = conectar()
    ultima_operacion = 0

    while True:
        try:
            # 🔥 RECONEXIÓN AUTOMÁTICA
            if not iq.check_connect():
                print("🔄 Reconectando...")
                iq = conectar()

            # 🔥 CONTROL DE SOBREOPERACIÓN
            if time.time() - ultima_operacion < 30:
                time.sleep(0.3)
                continue

            # 🔥 OBTENER PARES OTC ABIERTOS
            pares = obtener_pares_otc(iq)

            if not pares:
                time.sleep(1)
                continue

            data = {}

            # 🔥 SOLO PARES VÁLIDOS
            for par in pares:
                velas = obtener_velas(iq, par)

                if len(velas) > 50:
                    data[par] = velas

                time.sleep(0.1)  # evitar saturación

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                if operar(iq, par, direccion):
                    ultima_operacion = time.time()
                    time.sleep(60)

            else:
                time.sleep(0.3)

        except Exception as e:
            print("Error general:", e)
            iq = conectar()
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
