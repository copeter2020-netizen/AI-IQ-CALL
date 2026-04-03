import time
import requests
from iqoptionapi.stable_api import IQ_Option

# =========================
# 🔐 CONFIGURACIÓN
# =========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TELEGRAM_TOKEN = "TU_TOKEN"
CHAT_ID = "TU_CHAT_ID"

# 💰 IMPORTE
MONTO = 10  # ← CAMBIA AQUÍ

PARES = [
    "EURGBP-OTC",
    "EURJPY-OTC",
    "EURUSD-OTC",
    "GBPUSD-OTC",
    "USDCHF-OTC"
]

TIMEFRAME = 60
EXPIRACION = 1

# =========================
# 📩 TELEGRAM
# =========================
def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        pass

# =========================
# 🔌 CONEXIÓN ESTABLE
# =========================
def conectar():
    while True:
        try:
            print("🔄 Conectando a IQ Option...")
            iq = IQ_Option(EMAIL, PASSWORD)

            time.sleep(3)

            status, reason = iq.connect()

            if status:
                print("✅ Conectado correctamente")
                iq.change_balance("PRACTICE")
                time.sleep(2)
                return iq
            else:
                print("❌ Error conexión:", reason)

        except Exception as e:
            print("⚠️ Excepción:", e)

        print("⏳ Reintentando en 15s...")
        time.sleep(15)

# =========================
# 📊 OBTENER VELAS
# =========================
def get_velas(iq, par):
    try:
        return iq.get_candles(par, TIMEFRAME, 50, time.time())
    except:
        return None

# =========================
# 🧠 ESTRATEGIA
# =========================
def estrategia(velas):
    try:
        if not velas or len(velas) < 30:
            return None

        v = velas[-1]

        o = float(v.get("open", 0))
        c = float(v.get("close", 0))
        h = float(v.get("max", 0))
        l = float(v.get("min", 0))

        rango = h - l
        if rango <= 0:
            return None

        cuerpo = abs(c - o)
        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        # 🔥 fuerza real
        fuerza = cuerpo > rango * 0.6

        # 🔥 evitar lateral
        altos = [x["max"] for x in velas[-10:]]
        bajos = [x["min"] for x in velas[-10:]]

        if max(altos) - min(bajos) < rango * 3:
            return None

        # 🔥 rechazo
        rechazo_venta = mecha_sup > cuerpo * 1.5
        rechazo_compra = mecha_inf > cuerpo * 1.5

        # 🔥 continuidad
        ultimas = velas[-4:]
        alcistas = sum(1 for x in ultimas if x["close"] > x["open"])
        bajistas = sum(1 for x in ultimas if x["close"] < x["open"])

        # 🎯 decisión
        if fuerza and alcistas >= 3 and not rechazo_venta:
            return "call"

        if fuerza and bajistas >= 3 and not rechazo_compra:
            return "put"

        if rechazo_venta:
            return "put"

        if rechazo_compra:
            return "call"

        return None

    except Exception as e:
        print("❌ Error estrategia:", e)
        return None

# =========================
# ⏱ ENTRADA EN SEGUNDO 59
# =========================
def esperar_entrada():
    while True:
        if time.localtime().tm_sec >= 58:
            break
        time.sleep(0.2)

# =========================
# 💓 KEEP ALIVE
# =========================
def heartbeat():
    print("💓 activo:", time.strftime("%H:%M:%S"))

# =========================
# 🚀 BOT PRINCIPAL
# =========================
def run():
    iq = conectar()

    while True:
        try:
            heartbeat()

            if not iq.check_connect():
                print("⚠️ Reconectando sesión...")
                iq = conectar()
                continue

            for par in PARES:
                velas = get_velas(iq, par)
                if not velas:
                    continue

                señal = estrategia(velas)

                if señal:
                    print(f"🔥 {par} → {señal.upper()}")

                    enviar_telegram(
                        f"📡 SEÑAL\n{par}\n{señal.upper()}\n💰 ${MONTO}\n⏱ 1 MIN"
                    )

                    esperar_entrada()

                    check, _ = iq.buy(MONTO, par, señal, EXPIRACION)

                    if check:
                        print("✅ Operación ejecutada")
                    else:
                        print("❌ Error al ejecutar operación")

            time.sleep(1)

        except Exception as e:
            print("❌ ERROR GENERAL:", e)
            time.sleep(5)

# =========================
# ▶️ INICIO
# =========================
if __name__ == "__main__":
    run()
