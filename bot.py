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

MONTO = 30
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "GBPJPY-OTC",
    "USDCHF-OTC"
]

# 🔥 CONTROL GLOBAL
ultima_senal = None


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
# TIMING PRECISO (NO TOCAR)
# =========================
def esperar_apertura_real():
    while True:
        ahora = time.time()
        segundos = int(ahora) % 60
        milisegundos = ahora - int(ahora)

        # 🔥 Entrada ultra precisa
        if segundos == 58 and milisegundos >= 0.95:
            return

        time.sleep(0.002)


# =========================
# OBTENER VELAS
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
# FILTRO MERCADO MUERTO
# =========================
def mercado_activo(velas):
    if not velas:
        return False

    ultima = velas[-1]
    rango = ultima["max"] - ultima["min"]

    return rango > 0.00015


# =========================
# CONFIRMACIÓN FINAL
# =========================
def confirmar_direccion(velas, direccion):
    ultima = velas[-1]

    if ultima["close"] > ultima["open"]:
        confirmacion = "call"
    else:
        confirmacion = "put"

    return confirmacion == direccion


# =========================
# OPERAR (DIGITAL OTC)
# =========================
def operar(iq, par, direccion):
    try:
        esperar_apertura_real()

        iq.subscribe_strike_list(par, 1)
        time.sleep(0.2)

        status, order_id = iq.buy_digital_spot(par, MONTO, direccion, 1)

        iq.unsubscribe_strike_list(par, 1)

        if status:
            print(f"🚀 DIGITAL {par} {direccion}")

            enviar_mensaje(f"""
🚀 ENTRADA DIGITAL

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}

⏱ Entrada precisa (segundo 58)
""")
        else:
            print("❌ No ejecutó operación")

    except Exception as e:
        print("Error operar:", e)


# =========================
# MAIN
# =========================
def run():
    global ultima_senal

    if detectar_entrada_oculta is None:
        print("❌ No se puede ejecutar sin estrategia.py")
        return

    iq = conectar()

    while True:
        try:
            data = {}

            for par in PARES:
                velas = obtener_velas(iq, par)
                data[par] = velas

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                # 🔥 FILTRO DE CALIDAD
                if score < 75:
                    continue

                # 🔥 EVITAR REPETICIÓN
                if señal == ultima_senal:
                    continue

                # 🔥 FILTRO MERCADO
                if not mercado_activo(data[par]):
                    print(f"⚠️ Mercado muerto {par}")
                    continue

                # 🔥 CONFIRMACIÓN FINAL
                if not confirmar_direccion(data[par], direccion):
                    print(f"❌ Sin confirmación {par}")
                    continue

                print(f"🎯 Señal {par} {direccion} Score:{score}")

                operar(iq, par, direccion)

                ultima_senal = señal

                time.sleep(60)

            else:
                time.sleep(0.1)

        except Exception as e:
            print("Error loop:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
