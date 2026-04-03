import time
import json
import requests
from telegram import enviar_mensaje

API_URL = "https://api.example.com/price"  # reemplaza si usas API real

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

MONTO = 15  # 👈 AQUÍ CAMBIAS EL IMPORTE

# =========================
# 🔥 CONEXIÓN ESTABLE
# =========================
def get_data():
    try:
        r = requests.get(API_URL, timeout=5)

        if r.status_code != 200:
            return None

        data = r.json()

        # evitar error lastPrice
        if "lastPrice" not in data:
            return None

        return float(data["lastPrice"])

    except:
        return None


# =========================
# 🔥 ESTRATEGIA PRO
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

    # FILTRO ULTRA
    if fuerza < 0.6:
        return None

    # DIRECCIÓN
    if c > o and mecha_sup < cuerpo * 0.3:
        return "call"

    if c < o and mecha_inf < cuerpo * 0.3:
        return "put"

    return None


# =========================
# 🔥 EJECUCIÓN
# =========================
def ejecutar_operacion(par, direccion):
    print(f"📊 {par} → {direccion.upper()}")

    enviar_mensaje(f"""
🚀 ENTRADA DETECTADA

Par: {par}
Dirección: {direccion.upper()}
Expiración: 1 MIN
Monto: ${MONTO}
""")


# =========================
# 🔥 LOOP PRINCIPAL
# =========================
def run():

    while True:
        try:

            print("🔄 Buscando condiciones perfectas...")

            for par in PARES:

                velas = obtener_velas_fake()  # reemplaza por tu fuente real

                señal = detectar_entrada(velas)

                if señal:

                    print("🔥 CONDICIÓN PERFECTA")

                    # ⏱️ ENTRADA EN SEGUNDO 59
                    segundos = int(time.time()) % 60
                    esperar = 59 - segundos

                    if esperar > 0:
                        time.sleep(esperar)

                    ejecutar_operacion(par, señal)

                    time.sleep(60)  # evita sobreoperar

            time.sleep(5)

        except Exception as e:
            print("⚠️ Error:", e)
            time.sleep(10)


# =========================
# FAKE DATA (REEMPLAZAR)
# =========================
def obtener_velas_fake():
    velas = []
    for i in range(20):
        velas.append({
            "open": 1.0,
            "close": 1.1,
            "max": 1.2,
            "min": 0.9
        })
    return velas


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
