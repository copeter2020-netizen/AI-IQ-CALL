import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

# ================= CONFIG =================

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

PARES = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC"
]

MONTO = 5
TIEMPO = 1

# ==========================================


# ===== TELEGRAM =====
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass


# ===== CONEXIÓN ROBUSTA =====
def conectar():
    while True:
        try:
            print("🔄 Intentando conectar...")
            Iq = IQ_Option(EMAIL, PASSWORD)
            Iq.connect()

            if Iq.check_connect():
                print("✅ Conectado")
                enviar_telegram("🤖 BOT ACTIVO")
                return Iq
            else:
                print("❌ Fallo conexión, reintentando...")

        except Exception as e:
            print("ERROR conexión:", e)

        time.sleep(5)


# ===== VERIFICAR CONEXIÓN =====
def asegurar_conexion(Iq):
    if not Iq.check_connect():
        print("🔄 Reconectando...")
        return conectar()
    return Iq


# ===== OBTENER VELAS =====
def obtener_velas(Iq, par):
    try:
        velas = Iq.get_candles(par, 60, 50, time.time())

        if isinstance(velas, tuple):
            velas = velas[1]

        return velas

    except:
        return None


# ===== ESPERA CIERRE =====
def esperar_cierre():
    while True:
        segundos = int(time.time()) % 60

        if segundos >= 59.8:
            return

        time.sleep(0.2)


# ===== OPERAR =====
def operar(Iq, par, direccion):
    try:
        direccion = direccion.lower()

        status, _ = Iq.buy(MONTO, par, direccion, TIEMPO)

        if status:
            print(f"✅ {par} {direccion}")

            enviar_telegram(
                f"📊 SEÑAL\n"
                f"{par}\n"
                f"{direccion.upper()} - 1 MIN"
            )

        else:
            print("❌ Error al operar")

    except Exception as e:
        print("Error trade:", e)


# ===== LOOP PRINCIPAL =====
def loop():
    Iq = conectar()

    while True:
        try:
            Iq = asegurar_conexion(Iq)

            for par in PARES:

                velas = obtener_velas(Iq, par)

                if not velas or len(velas) < 20:
                    continue

                señal = detectar_entrada(velas)

                if señal:

                    esperar_cierre()

                    velas = obtener_velas(Iq, par)
                    confirmacion = detectar_entrada(velas)

                    if confirmacion == señal:
                        operar(Iq, par, señal)

                time.sleep(1)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(3)


# ===== START =====
if __name__ == "__main__":
    loop()
