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

MONTO = 4
CUENTA = "PRACTICE"

PARES = ["EURUSD", "EURJPY"]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except:
        pass


# =========================
# CONEXIÓN SEGURA
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)
                print("✅ CONECTADO")
                return iq
        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# VALIDAR PAR ABIERTO
# =========================
def par_abierto(iq, par):
    try:
        activos = iq.get_all_open_time()
        return activos["digital"][par]["open"]
    except:
        return False


# =========================
# OBTENER VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 50, time.time())

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
# OPERAR SEGURO
# =========================
def operar(iq, par, direccion):

    # 🔒 VALIDAR PAR
    if not par_abierto(iq, par):
        print(f"❌ {par} cerrado")
        return

    print(f"🚀 OPERANDO {par} {direccion}")

    try:
        check, id = iq.buy(MONTO, par, direccion, 5)

        if check:
            print("✅ OPERACIÓN EJECUTADA")

            enviar_mensaje(f"""
🚀 ENTRADA REAL

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}
""")
        else:
            print("❌ Falló ejecución")

    except Exception as e:
        print("❌ ERROR OPERANDO:", e)


# =========================
# RECONEXIÓN AUTOMÁTICA
# =========================
def asegurar_conexion(iq):
    if not iq.check_connect():
        print("🔄 RECONECTANDO...")
        return conectar()
    return iq


# =========================
# LOOP PRINCIPAL
# =========================
def run():

    iq = conectar()

    while True:
        try:
            iq = asegurar_conexion(iq)

            data = {}

            for par in PARES:
                if par_abierto(iq, par):
                    velas = obtener_velas(iq, par)
                    if velas:
                        data[par] = velas

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                time.sleep(300)  # 5 minutos

            else:
                time.sleep(0.5)

        except Exception as e:
            print("❌ ERROR GENERAL:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
