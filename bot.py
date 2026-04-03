import time
import datetime
import requests
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

PARES = [
    "EURGBP-OTC",
    "EURJPY-OTC",
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC"
]

MONTO = 15
EXP = 1

# ==========================
# TELEGRAM
# ==========================
def telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ==========================
# CONEXIÓN ROBUSTA
# ==========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)

            iq.connect()

            time.sleep(3)

            if iq.check_connect():
                print("✅ Conectado correctamente")

                iq.change_balance("PRACTICE")

                return iq
            else:
                print("❌ No conecta, retry...")
                time.sleep(5)

        except Exception as e:
            print("ERROR conexión:", e)
            time.sleep(5)

# ==========================
# KEEP ALIVE (ANTI RAILWAY KILL)
# ==========================
def keep_alive(iq):
    try:
        iq.get_balance()
    except:
        pass

# ==========================
# ESPERA 59
# ==========================
def esperar_59():
    while True:
        if datetime.datetime.now().second >= 59:
            break
        time.sleep(0.05)

# ==========================
# BOT
# ==========================
def run():
    iq = conectar()

    ultimo_keepalive = time.time()

    while True:
        try:
            # 🔥 mantener conexión viva
            if time.time() - ultimo_keepalive > 30:
                keep_alive(iq)
                ultimo_keepalive = time.time()

            # 🔥 reconectar si se cae
            if not iq.check_connect():
                print("⚠️ Reconectando...")
                iq = conectar()

            operacion = None

            for par in PARES:
                try:
                    velas = iq.get_candles(par, 60, 60, time.time())
                except:
                    continue

                señal = detectar_entrada(velas)

                if señal:
                    operacion = (par, señal)
                    break

            if operacion:
                par, señal = operacion

                print(f"🎯 CONDICIÓN PERFECTA: {par} {señal}")

                esperar_59()

                check, _ = iq.buy(MONTO, par, señal, EXP)

                if check:
                    msg = f"🔥 SNIPER\n{par}\n{señal.upper()}\nM1"
                    print(msg)
                    telegram(msg)
                else:
                    print("❌ Error al ejecutar")

            else:
                print("⏳ Sin condiciones perfectas...")

            time.sleep(2)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)

run()
