import time
from iqoptionapi.stable_api import IQ_Option
from telegram import enviar_mensaje

# =========================
# 🔐 CONFIG
# =========================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

MONTO = 12

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
# 🔌 CONEXIÓN ROBUSTA
# =========================
def conectar():
    while True:
        try:
            print("🔄 Conectando...")
            iq = IQ_Option(EMAIL, PASSWORD)

            time.sleep(3)

            status, reason = iq.connect()

            if status:
                print("✅ Conectado")
                iq.change_balance("PRACTICE")
                return iq

            # 🔴 ERROR CREDENCIALES
            if "invalid_credentials" in str(reason):
                print("❌ EMAIL O PASSWORD INCORRECTO")
                enviar_mensaje("❌ ERROR LOGIN IQ OPTION")
                time.sleep(60)
                continue

            print("❌ Error:", reason)

        except Exception as e:
            print("⚠️ Error conexión:", e)

        print("⏳ Reintentando en 15s...")
        time.sleep(15)

# =========================
# 📊 VELAS
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

        o = float(v["open"])
        c = float(v["close"])
        h = float(v["max"])
        l = float(v["min"])

        rango = h - l
        if rango <= 0:
            return None

        cuerpo = abs(c - o)
        mecha_sup = h - max(o, c)
        mecha_inf = min(o, c) - l

        fuerza = cuerpo > rango * 0.6

        altos = [x["max"] for x in velas[-10:]]
        bajos = [x["min"] for x in velas[-10:]]

        if max(altos) - min(bajos) < rango * 3:
            return None

        rechazo_venta = mecha_sup > cuerpo * 1.5
        rechazo_compra = mecha_inf > cuerpo * 1.5

        ultimas = velas[-4:]
        alcistas = sum(1 for x in ultimas if x["close"] > x["open"])
        bajistas = sum(1 for x in ultimas if x["close"] < x["open"])

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
# ⏱ ENTRADA EXACTA
# =========================
def esperar_entrada():
    while True:
        if time.localtime().tm_sec >= 58:
            break
        time.sleep(0.2)

# =========================
# 💓 HEARTBEAT
# =========================
def heartbeat():
    print("💓 activo:", time.strftime("%H:%M:%S"))

# =========================
# 🚀 BOT
# =========================
def run():
    iq = conectar()

    while True:
        try:
            heartbeat()

            if not iq.check_connect():
                print("⚠️ Reconectando...")
                iq = conectar()
                continue

            for par in PARES:
                velas = get_velas(iq, par)
                if not velas:
                    continue

                señal = estrategia(velas)

                if señal:
                    print(f"🔥 {par} → {señal.upper()}")

                    enviar_mensaje(
                        f"📡 SEÑAL\n{par}\n{señal.upper()}\n💰 ${MONTO}\n⏱ 1 MIN"
                    )

                    esperar_entrada()

                    check, _ = iq.buy(MONTO, par, señal, EXPIRACION)

                    if check:
                        print("✅ Operación ejecutada")
                    else:
                        print("❌ Error operación")

            time.sleep(1)

        except Exception as e:
            print("❌ ERROR:", e)
            time.sleep(5)

# =========================
# ▶️ INICIO
# =========================
if __name__ == "__main__":
    run()
