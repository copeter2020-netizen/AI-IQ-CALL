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

MONTO = 10
CUENTA = "PRACTICE"

PARES = [
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "EURJPY-OTC",
    "EURGBP-OTC",
    "USDCHF-OTC"
]

# =========================
# TELEGRAM (SIN LIBRERÍA)
# =========================
def enviar_mensaje(texto):
    try:
        if not TOKEN or not CHAT_ID:
            print("⚠️ Telegram no configurado")
            return

        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": texto
        }, timeout=5)

    except Exception as e:
        print("Error Telegram:", e)


# =========================
# CONEXIÓN ESTABLE PRO
# =========================
def conectar():

    while True:
        try:
            if not EMAIL or not PASSWORD:
                print("❌ Faltan credenciales en Railway")
                time.sleep(10)
                continue

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
# VELAS REALES
# =========================
def obtener_velas(iq, par):
    try:
        velas = iq.get_candles(par, 60, 20, time.time())

        if not velas:
            return []

        resultado = []
        for v in velas:
            resultado.append({
                "open": v.get("open", 0),
                "close": v.get("close", 0),
                "max": v.get("max", 0),
                "min": v.get("min", 0)
            })

        return resultado

    except Exception as e:
        print("Error velas:", e)
        return []


# =========================
# ESTRATEGIA (CORREGIDA)
# =========================
def detectar_entrada(velas, *_):  # ✅ acepta extra argumentos (FIX ERROR)

    try:
        if len(velas) < 20:
            return None

        v = velas[-1]

        o = float(v["open"])
        c = float(v["close"])
        h = float(v["max"])
        l = float(v["min"])

        rango = h - l
        if rango == 0:
            return None

        cuerpo = abs(c - o)
        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        fuerza = cuerpo / rango

        # 🔥 FILTRO ULTRA SELECTIVO
        if fuerza < 0.65:
            return None

        # 🔥 EVITA LATERAL
        if mecha_sup > cuerpo or mecha_inf > cuerpo:
            return None

        if c > o:
            return "call"

        if c < o:
            return "put"

        return None

    except Exception as e:
        print("Error estrategia:", e)
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
🚀 ENTRADA PRO

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
# LOOP PRINCIPAL
# =========================
def run():

    iq = conectar()

    while True:
        try:

            if not iq.check_connect():
                print("🔄 Reconectando...")
                iq = conectar()

            print("🔎 Buscando condiciones PERFECTAS...")

            for par in PARES:

                velas = obtener_velas(iq, par)

                señal = detectar_entrada(velas)  # ✅ YA NO FALLA

                if señal:

                    print("✅ CONDICIÓN PERFECTA")

                    # ⏱️ ENTRADA SEGUNDO 59
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
