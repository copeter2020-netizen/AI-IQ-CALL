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

MONTO = 3000
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
# TIMING PERFECTO
# =========================
def esperar_apertura_real():
    while True:
        ahora = time.time()
        segundos = int(ahora) % 60
        milisegundos = ahora - int(ahora)

        if segundos == 59 and milisegundos > 0.90:
            return

        time.sleep(0.002)


# =========================
# DATOS
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
# OPERACIÓN
# =========================
def operar(iq, par, direccion):

    try:
        esperar_apertura_real()

        check, _ = iq.buy(MONTO, par, direccion, 3)

        if check:
            print(f"🚀 ENTRADA {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 3 MIN
Monto: ${MONTO}

⏱ Entrada en apertura REAL
""")

    except Exception as e:
        print("Error operar:", e)


# =========================
# LOOP ULTRA RÁPIDO 🔥
# =========================
def run():

    if detectar_entrada_oculta is None:
        print("❌ No se puede ejecutar sin estrategia.py")
        return

    iq = conectar()

    operados = {}  # 🔥 evita duplicar entradas por vela

    while True:
        try:
            ahora = int(time.time())
            vela_actual = ahora // 60

            data = {}

            for par in PARES:
                data[par] = obtener_velas(iq, par)

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                # 🔥 evitar repetir en misma vela
                if operados.get(par) == vela_actual:
                    time.sleep(0.2)
                    continue

                operados[par] = vela_actual

                print(f"🎯 Señal {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

            time.sleep(0.2)

        except Exception as e:
            print("Error loop:", e)
            time.sleep(3)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
