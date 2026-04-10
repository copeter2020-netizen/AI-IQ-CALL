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
# CONEXIÓN (ANTI CRASH)
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                iq.change_balance(CUENTA)

                # 🔥 EVITA ERRORES UNDERLYING
                iq.api.digital_option = None

                print("✅ CONECTADO ESTABLE")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# OBTENER VELAS (SEGURO)
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

    except Exception as e:
        print(f"❌ Error velas {par}:", e)
        return None


# =========================
# VALIDAR PAR REAL
# =========================
def par_valido(iq, par):
    try:
        velas = iq.get_candles(par, 60, 1, time.time())
        return velas is not None and len(velas) > 0
    except:
        return False


# =========================
# OPERAR (ULTRA SEGURO)
# =========================
def operar(iq, par, direccion):

    if not par_valido(iq, par):
        print(f"⛔ {par} inválido")
        return False

    try:
        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        if status:
            print(f"🚀 {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA EJECUTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}
""")

            return True

        else:
            print(f"❌ Fallo entrada {par}")

    except Exception as e:
        print(f"❌ Error operar {par}:", e)

        # 🔥 SI FALLA → REINICIAR CONEXIÓN
        return False

    return False


# =========================
# MAIN (ANTI CRASH TOTAL)
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

                time.sleep(0.3)  # 🔥 evita saturación

            if not data:
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                if operar(iq, par, direccion):
                    ultima_operacion = time.time()
                    time.sleep(60)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("❌ ERROR GLOBAL:", e)

            # 🔥 REINICIO TOTAL (CLAVE)
            iq = conectar()
            time.sleep(5)


if __name__ == "__main__":
    run()
