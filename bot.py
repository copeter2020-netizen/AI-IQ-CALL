import time
import os
import requests
from iqoptionapi.stable_api import IQ_Option

# =========================
# VARIABLES RAILWAY
# =========================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MONTO = 3
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

# =========================
# TELEGRAM
# =========================
def enviar_mensaje(texto):
    try:
        if not TOKEN or not CHAT_ID:
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)

    except Exception as e:
        print("Telegram error:", e)


# =========================
# CONEXIÓN
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
                print("❌ Credenciales incorrectas")
                time.sleep(10)

        except Exception as e:
            print("Error conexión:", e)
            time.sleep(10)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 30, time.time())

        return [{
            "open": v["open"],
            "close": v["close"],
            "max": v["max"],
            "min": v["min"]
        } for v in velas]

    except:
        return []


# =========================
# 🔥 ESTRATEGIA ULTRA PRO
# =========================
def detectar_entrada(velas, *_):

    if len(velas) < 30:
        return None

    v1 = velas[-1]
    v2 = velas[-2]
    v3 = velas[-3]
    v4 = velas[-4]

    def datos(v):
        return float(v["open"]), float(v["close"]), float(v["max"]), float(v["min"])

    o1,c1,h1,l1 = datos(v1)
    o2,c2,_,_ = datos(v2)
    o3,c3,_,_ = datos(v3)
    o4,c4,_,_ = datos(v4)

    rango = h1 - l1
    if rango == 0:
        return None

    cuerpo = abs(c1 - o1)
    fuerza = cuerpo / rango

    mecha_sup = h1 - max(o1, c1)
    mecha_inf = min(o1, c1) - l1

    # =========================
    # 🔥 1. FUERZA EXTREMA
    # =========================
    if fuerza < 0.8:
        return None

    # =========================
    # 🔥 2. SIN RECHAZO
    # =========================
    if mecha_sup > cuerpo * 0.6 or mecha_inf > cuerpo * 0.6:
        return None

    # =========================
    # 🔥 3. 4 VELAS MISMA DIRECCIÓN
    # =========================
    alcista = c1>o1 and c2>o2 and c3>o3 and c4>o4
    bajista = c1<o1 and c2<o2 and c3<o3 and c4<o4

    if not alcista and not bajista:
        return None

    # =========================
    # 🔥 4. IMPULSO REAL
    # =========================
    impulso = abs(c1 - o4)
    if impulso < rango * 2:
        return None

    # =========================
    # 🔥 5. EVITA LATERAL (estructura)
    # =========================
    maximos = [v["max"] for v in velas[-10:]]
    minimos = [v["min"] for v in velas[-10:]]

    if max(maximos) - min(minimos) < rango * 3:
        return None

    # =========================
    # 🔥 DECISIÓN FINAL
    # =========================
    if alcista:
        return "call"

    if bajista:
        return "put"

    return None


# =========================
# OPERAR
# =========================
def operar(iq, par, direccion):

    try:
        print(f"🔥 {par} → {direccion}")

        check, _ = iq.buy(MONTO, par, direccion, 1)

        if check:
            print("✅ OPERACIÓN ABIERTA")

            enviar_mensaje(f"""
🚀 ENTRADA ULTRA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}
""")
        else:
            print("❌ No ejecutada")

    except Exception as e:
        print("Error operación:", e)


# =========================
# LOOP
# =========================
def run():

    iq = conectar()

    while True:
        try:

            if not iq.check_connect():
                iq = conectar()

            print("🔎 Buscando condiciones PERFECTAS...")

            for par in PARES:

                velas = obtener_velas(iq, par)

                señal = detectar_entrada(velas)

                if señal:

                    print("✅ CONDICIÓN PERFECTA")

                    segundos = int(time.time()) % 60
                    esperar = 59 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    operar(iq, par, señal)

                    time.sleep(60)

            time.sleep(5)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(10)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
