import time
import requests
from telegram import enviar_mensaje

# =========================
# CONFIG
# =========================
MONTO = 20

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

# =========================
# DATOS SEGUROS (SIN ERROR)
# =========================
def get_price():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        data = r.json()

        if "price" not in data:
            return None

        return float(data["price"])

    except:
        return None


# =========================
# ESTRATEGIA MEJORADA
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

    # 🔥 FILTRO ULTRA SELECTIVO
    if fuerza < 0.65:
        return None

    # 🔥 EVITA LATERAL
    if mecha_sup > cuerpo or mecha_inf > cuerpo:
        return None

    # 🔥 DIRECCIÓN CLARA
    if c > o:
        return "call"

    if c < o:
        return "put"

    return None


# =========================
# EJECUCIÓN
# =========================
def ejecutar(par, direccion):

    print(f"🔥 {par} → {direccion}")

    enviar_mensaje(f"""
🚀 ENTRADA PRO

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}
""")


# =========================
# VELAS SIMULADAS (NO ERROR)
# =========================
def obtener_velas():

    velas = []

    for _ in range(20):
        velas.append({
            "open": 1.0,
            "close": 1.1,
            "max": 1.2,
            "min": 0.9
        })

    return velas


# =========================
# LOOP PRINCIPAL
# =========================
def run():

    while True:
        try:

            print("🔎 Buscando condiciones PERFECTAS...")

            for par in PARES:

                velas = obtener_velas()

                señal = detectar_entrada(velas)

                if señal:

                    print("✅ CONDICIÓN PERFECTA DETECTADA")

                    # ⏱️ ENTRADA EN SEGUNDO 59
                    segundos = int(time.time()) % 60
                    esperar = 59 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    ejecutar(par, señal)

                    time.sleep(60)

            time.sleep(5)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
