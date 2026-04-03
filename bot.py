import time
import requests
from iqoptionapi.stable_api import IQ_Option

# =========================
# CONFIG IQ OPTION
# =========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

MONTO = 2
CUENTA = "PRACTICE"  # PRACTICE o REAL

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

# =========================
# TELEGRAM (SIN ERROR)
# =========================
TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

def enviar_mensaje(texto):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


# =========================
# CONEXIÓN ESTABLE IQ
# =========================
def conectar():
    while True:
        try:
            iq = IQ_Option(EMAIL, PASSWORD)
            iq.connect()

            if iq.check_connect():
                print("✅ CONECTADO A IQ OPTION")
                iq.change_balance(CUENTA)
                return iq
            else:
                print("❌ Error credenciales")
                time.sleep(5)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(5)


# =========================
# OBTENER VELAS REALES
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 20, time.time())

        resultado = []
        for v in velas:
            resultado.append({
                "open": v["open"],
                "close": v["close"],
                "max": v["max"],
                "min": v["min"]
            })

        return resultado

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# ESTRATEGIA (MISMA TUYA)
# =========================
def detectar_entrada(velas):

    if len(velas) < 20:
        return None

    v = velas[-1]

    o = float(v["open"])
    c = float(v["close"])
    h = float(v["max"])
    l = float(v["min"])

    cuerpo = abs(c - o)
    rango = h - l

    if rango == 0:
        return None

    mecha_sup = h - max(o, c)
    mecha_inf = min(o, c) - l

    fuerza = cuerpo / rango

    if fuerza < 0.65:
        return None

    if mecha_sup > cuerpo or mecha_inf > cuerpo:
        return None

    if c > o:
        return "call"

    if c < o:
        return "put"

    return None


# =========================
# EJECUTAR OPERACIÓN
# =========================
def operar(iq, par, direccion):

    try:
        print(f"🔥 OPERANDO {par} → {direccion}")

        check, id = iq.buy(MONTO, par, direccion, 1)

        if check:
            print("✅ OPERACIÓN ABIERTA")

            enviar_mensaje(f"""
🚀 ENTRADA REAL

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}
""")
        else:
            print("❌ No se pudo abrir operación")

    except Exception as e:
        print("Error operación:", e)


# =========================
# LOOP PRINCIPAL
# =========================
def run():

    iq = conectar()

    while True:
        try:

            print("🔎 Buscando condiciones PERFECTAS...")

            for par in PARES:

                velas = obtener_velas(iq, par)

                señal = detectar_entrada(velas)  # ✅ CORREGIDO (solo 1 argumento)

                if señal:

                    print("✅ CONDICIÓN PERFECTA")

                    # ⏱️ segundo 59
                    segundos = int(time.time()) % 60
                    esperar = 59 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    operar(iq, par, señal)

                    time.sleep(60)

            time.sleep(3)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
