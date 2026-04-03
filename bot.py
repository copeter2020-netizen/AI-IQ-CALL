import time
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

# ================= CONFIG =================

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TELEGRAM_TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

PARES = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC"
]

MONTO = 2
TIEMPO = 1

# =========================================


# ===== TELEGRAM =====
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except Exception as e:
        print("Error Telegram:", e)


# ===== CONEXIÓN =====
def conectar():
    Iq = IQ_Option(EMAIL, PASSWORD)
    Iq.connect()

    if Iq.check_connect():
        print("✅ Conectado")
        enviar_telegram("🤖 BOT ACTIVO")
        return Iq
    else:
        print("❌ Error conexión")
        return None


# ===== OBTENER VELAS =====
def obtener_velas(Iq, par):
    velas = Iq.get_candles(par, 60, 50, time.time())

    if isinstance(velas, tuple):
        velas = velas[1]  # FIX ERROR

    return velas


# ===== ESPERA CIERRE =====
def esperar_cierre():
    while True:
        segundos = int(time.time()) % 60

        if segundos >= 58:  # entrada exacta
            return

        time.sleep(0.2)


# ===== OPERAR =====
def operar(Iq, par, direccion):
    direccion = direccion.lower()

    if direccion not in ["call", "put"]:
        return

    status, _ = Iq.buy(MONTO, par, direccion, TIEMPO)

    if status:
        print(f"✅ {par} {direccion.upper()}")

        enviar_telegram(
            f"📊 SEÑAL\n"
            f"Par: {par}\n"
            f"Dirección: {direccion.upper()}\n"
            f"Tiempo: 1 min"
        )
    else:
        print("❌ Error al operar")


# ===== LOOP =====
def loop():
    Iq = conectar()

    if Iq is None:
        return

    while True:
        try:
            for par in PARES:

                velas = obtener_velas(Iq, par)

                if not velas or len(velas) < 20:
                    continue

                señal = detectar_entrada(velas)

                if señal:

                    esperar_cierre()

                    # confirmación con nueva vela
                    velas = obtener_velas(Iq, par)
                    señal_final = detectar_entrada(velas)

                    if señal_final == señal:
                        operar(Iq, par, señal)

                time.sleep(1)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(3)


# ===== START =====
if __name__ == "__main__":
    loop()
