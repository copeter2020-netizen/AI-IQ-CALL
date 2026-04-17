import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 600
CUENTA = "PRACTICE"

ultima_entrada = 0


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
                print("✅ BOT CONECTADO")
                return iq
        except:
            pass
        time.sleep(5)


# =========================
# VALIDAR ACTIVO
# =========================
def activo_abierto(iq, par):
    try:
        return iq.get_all_open_time()["binary"][par]["open"]
    except:
        return True  # evitar falso cerrado OTC


# =========================
# ESPERAR MEJOR MOMENTO (🔥 NUEVO)
# =========================
def sincronizar_entrada():
    while True:
        segundos = int(time.time() % 60)
        if segundos >= 58:  # entrada casi en nueva vela
            break
        time.sleep(0.01)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par, timeframe):
    try:
        return iq.get_candles(par, timeframe, 50, time.time())
    except:
        return None


# =========================
# OPERAR (MEJORADO)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 10:
        return

    if not activo_abierto(iq, par):
        print(f"❌ {par} cerrado")
        return

    print(f"⏳ Esperando timing {par}...")
    sincronizar_entrada()  # 🔥 mejora de precisión

    # 🔥 reintentos reales
    for intento in range(3):
        try:
            status, order_id = iq.buy(MONTO, par, direccion, 1)

            if status:
                print(f"🚀 {par} {direccion} | ID: {order_id}")
                ultima_entrada = time.time()
                return
            else:
                print("⚠️ Reintentando ejecución...")

        except Exception as e:
            print("Error:", e)

        time.sleep(0.5)

    print("❌ Falló la ejecución total")


# =========================
# MAIN
# =========================
def run():
    iq = conectar()

    PARES = [
        "EURUSD-OTC",
        "GBPUSD-OTC",
        "USDJPY-OTC",
        "USDCHF-OTC",
        "EURJPY-OTC",
        "GBPJPY-OTC"
    ]

    while True:
        try:
            data = {}

            for par in PARES:

                m1 = obtener_velas(iq, par, 60)
                m5 = obtener_velas(iq, par, 300)

                if m1 and m5:
                    data[par] = {"m1": m1, "m5": m5}

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"""
📊 SEÑAL DETECTADA
{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    run()
