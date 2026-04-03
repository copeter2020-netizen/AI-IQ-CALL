import time
import datetime
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

# ==========================
# 🔐 CONFIG
# ==========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TELEGRAM_TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

PARES = [
    "EURGBP-OTC",
    "EURJPY-OTC",
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC"
]

MONTO = 2
EXPIRACION = 1

# ==========================
# 📩 TELEGRAM
# ==========================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ==========================
# ⏱️ ESPERA SEGUNDO 59
# ==========================
def esperar_entrada():
    while True:
        now = datetime.datetime.now()
        if now.second >= 59:
            break
        time.sleep(0.2)

# ==========================
# 📊 OBTENER VELAS
# ==========================
def get_velas(iq, par):
    velas = iq.get_candles(par, 60, 50, time.time())
    return velas

# ==========================
# 🚀 EJECUCIÓN
# ==========================
def run():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    if not iq.check_connect():
        print("❌ Error conectando")
        return

    print("✅ Conectado a IQ Option")

    while True:
        try:
            mejor_par = None
            mejor_senal = None

            # ==========================
            # 🔍 ANALISIS MULTIPAR
            # ==========================
            for par in PARES:
                velas = get_velas(iq, par)

                señal = detectar_entrada(velas)

                if señal:
                    mejor_par = par
                    mejor_senal = señal
                    break  # 🔥 solo 1 operación perfecta

            # ==========================
            # 🎯 EJECUCIÓN SNIPER
            # ==========================
            if mejor_senal:
                print(f"🎯 Señal detectada: {mejor_par} -> {mejor_senal}")

                esperar_entrada()

                check, id = iq.buy(MONTO, mejor_par, mejor_senal, EXPIRACION)

                if check:
                    msg = f"🔥 ENTRADA\n{mejor_par}\n{mejor_senal.upper()}\n⏱ M1"
                    print(msg)
                    enviar_telegram(msg)
                else:
                    print("❌ Error al ejecutar")

            else:
                print("⏳ Sin condiciones perfectas...")

            time.sleep(2)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)

run()
