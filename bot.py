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

# 🔥 CONTROL TELEGRAM
BOT_ACTIVO = True
LAST_UPDATE_ID = 0

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]


# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    if not TOKEN or not CHAT_ID:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": texto},
            timeout=5
        )
    except:
        pass


def leer_comandos():
    global BOT_ACTIVO, LAST_UPDATE_ID

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={LAST_UPDATE_ID + 1}"
        res = requests.get(url, timeout=5).json()

        for update in res.get("result", []):
            LAST_UPDATE_ID = update["update_id"]

            if "message" not in update:
                continue

            texto = update["message"].get("text", "").lower()

            if "/stop" in texto:
                BOT_ACTIVO = False
                enviar_mensaje("⛔ BOT DETENIDO")

            elif "/start" in texto:
                BOT_ACTIVO = True
                enviar_mensaje("✅ BOT ACTIVADO")

    except:
        pass


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
                print("✅ CONECTADO")
                enviar_mensaje("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# VALIDAR OTC
# =========================
def par_disponible(iq, par):
    try:
        activos = iq.get_all_open_time()

        if "digital" not in activos:
            return False

        if par not in activos["digital"]:
            return False

        return activos["digital"][par]["open"]

    except:
        return False


# =========================
# TIMING
# =========================
def esperar_apertura_real():
    while True:
        ahora = time.time()
        segundos = int(ahora) % 60
        milisegundos = ahora - int(ahora)

        if segundos == 58 and milisegundos > 0.90:
            return

        time.sleep(0.005)


# =========================
# DATOS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 40, time.time())

        if not velas or len(velas) < 30:
            return None

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print("Error velas:", e)
        return None


# =========================
# OPERAR (SIN UNDERLYING)
# =========================
def operar(iq, par, direccion):

    if not par_disponible(iq, par):
        print(f"❌ {par} no disponible")
        return False

    esperar_apertura_real()

    try:
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 5)

        if status:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 5 MIN
Monto: ${MONTO}

⏱ Entrada en apertura REAL
""")
            return True

    except Exception as e:
        print("Error operar:", e)

    return False


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ No se puede ejecutar sin estrategia.py")
        return

    iq = conectar()

    while True:
        try:
            leer_comandos()  # 🔥 escucha telegram SIEMPRE

            if not BOT_ACTIVO:
                time.sleep(1)
                continue

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

                print(f"🎯 Señal {par} {direccion} Score:{score}")

                if operar(iq, par, direccion):
                    time.sleep(180)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error loop:", e)
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
