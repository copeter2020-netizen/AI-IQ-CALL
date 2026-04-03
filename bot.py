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
# CONEXIÓN ULTRA ESTABLE
# ==========================
def conectar():
    intentos = 0

    while True:
        try:
            print("🔄 Conectando...")

            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            time.sleep(5)

            if iq.check_connect():
                print("✅ Conectado OK")

                iq.change_balance("PRACTICE")

                return iq

            else:
                print("❌ Fallo conexión")

        except Exception as e:
            print("⚠️ Error conexión:", e)

        intentos += 1

        # 🔥 evitar bloqueo IQ Option
        espera = min(10 + intentos * 2, 60)
        print(f"⏳ Reintentando en {espera}s...")
        time.sleep(espera)

# ==========================
# KEEP ALIVE
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
# OBTENER VELAS SEGURO
# ==========================
def get_velas_seguro(iq, par):
    try:
        velas = iq.get_candles(par, 60, 60, time.time())

        if not velas or len(velas) == 0:
            return None

        return velas

    except:
        return None

# ==========================
# BOT PRINCIPAL
# ==========================
def run():
    iq = conectar()

    last_keep = time.time()

    while True:
        try:
            # 🔥 mantener conexión viva
            if time.time() - last_keep > 25:
                keep_alive(iq)
                last_keep = time.time()

            # 🔥 reconectar si se cae
            if not iq.check_connect():
                print("⚠️ Reconectando sesión...")
                iq = conectar()
                continue

            operacion = None

            for par in PARES:
                velas = get_velas_seguro(iq, par)

                if velas is None:
                    continue

                señal = detectar_entrada(velas)

                if señal:
                    operacion = (par, señal)
                    break

            if operacion:
                par, señal = operacion

                print(f"🎯 PERFECTO: {par} {señal}")

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

            # 🔥 delay humano (clave)
            time.sleep(3)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(10)

run()
