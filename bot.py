import time
import os
import requests
import sys
from iqoptionapi.stable_api import IQ_Option

# =========================
# 🔥 FIX PATH (Railway)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

# =========================
# IMPORT
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

MONTO = 3000
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC", 
    "GBPJPY-OTC", 
    "AUDCAD-OTC"
]

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
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# 🔥 SEGUNDO 58 (SNIPER)
# =========================
def esperar_segundo_58():
    while True:
        segundos = int(time.time()) % 60

        if segundos >= 59:
            return

        time.sleep(0.1)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 40, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# 🔥 OPERAR (MEJORADO)
# =========================
def operar(iq, par, direccion):

    try:
        if not iq.check_connect():
            print("⚠️ Reconectando...")
            iq.connect()

        # ⏱️ Entrada SNIPER
        esperar_segundo_59()

        check, id = iq.buy(MONTO, par, direccion, 4)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA SNIPER

Par: {par}
Dirección: {direccion.upper()}
Expiración: 4 MIN
Monto: ${MONTO}

⏱ Entrada en segundo 59
""")

        else:
            print("❌ Falló ejecución")

    except Exception as e:
        print("Error operar:", e)


# =========================
# LOOP PRINCIPAL
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ No se puede ejecutar sin estrategia.py")
        return

    iq = conectar()

    ultima_operacion = 0  # 🔥 evita duplicar

    while True:
        try:

            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)

                if len(velas) < 30:
                    continue

                data[par] = velas

            señal = detectar_entrada_oculta(data)

            ahora = time.time()

            if señal and (ahora - ultima_operacion > 180):

                par, direccion, score = señal

                print(f"🎯 Señal {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                ultima_operacion = ahora

                time.sleep(5)

            else:
                time.sleep(0.5)

        except Exception as e:
            print("Error loop:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
