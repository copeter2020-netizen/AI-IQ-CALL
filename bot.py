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
                print("✅ CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# CACHE ACTIVOS (ANTI UNDERLYING)
# =========================
def obtener_activos(iq):
    try:
        return iq.get_all_open_time()
    except:
        return {}


# =========================
# FILTRAR PARES OTC ABIERTOS
# =========================
def obtener_pares_otc(activos):
    pares = []

    try:
        for par, info in activos.get("digital", {}).items():
            if "-OTC" in par and info.get("open"):
                pares.append(par)
    except:
        pass

    return pares


# =========================
# OBTENER VELAS (SEGURAS)
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 120, time.time())

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
# OPERAR (SIN ERROR UNDERLYING)
# =========================
def operar(iq, activos, par, direccion):

    try:
        # 🔥 VALIDACIÓN SEGURA
        if par not in activos.get("digital", {}):
            return False

        if not activos["digital"][par]["open"]:
            return False

        # 🔥 OPERACIÓN CONTROLADA
        status, _ = iq.buy_digital_spot(par, MONTO, direccion, 1)

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

    except Exception as e:
        print("Error operar:", e)

    return False


# =========================
# MAIN
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ Estrategia no disponible")
        return

    iq = conectar()
    ultima_operacion = 0
    activos_cache = {}
    tiempo_cache = 0

    while True:
        try:
            # 🔄 RECONEXIÓN
            if not iq.check_connect():
                print("🔄 Reconectando...")
                iq = conectar()

            # 🔥 ACTUALIZAR ACTIVOS CADA 30s
            if time.time() - tiempo_cache > 30:
                activos_cache = obtener_activos(iq)
                tiempo_cache = time.time()

            pares = obtener_pares_otc(activos_cache)

            if not pares:
                time.sleep(1)
                continue

            # 🔥 CONTROL DE OPERACIONES
            if time.time() - ultima_operacion < 30:
                time.sleep(0.3)
                continue

            data = {}

            for par in pares:
                velas = obtener_velas(iq, par)

                if len(velas) > 50:
                    data[par] = velas

                time.sleep(0.15)  # 🔥 evita crash IQ Option

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"🎯 {par} {direccion} Score:{score}")

                if operar(iq, activos_cache, par, direccion):
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
