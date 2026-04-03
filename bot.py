import time
import os
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada
import requests

# ================= CONFIG =================
EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TG_CHAT_ID")

PAR = "EURUSD-OTC"
MONTO = 2
TIEMPO = 1  # 1 minuto

# ==========================================

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
    except:
        pass

def conectar():
    while True:
        try:
            print("🔄 Conectando...")
            iq = IQ_Option(EMAIL.strip(), PASSWORD.strip())
            status, reason = iq.connect()

            if status:
                print("✅ Conectado a IQ Option")
                iq.change_balance("PRACTICE")
                return iq
            else:
                print(f"❌ Error: {reason}")

                if "invalid_credentials" in str(reason):
                    print("🚨 Credenciales incorrectas")
                    exit()

                time.sleep(10)

        except Exception as e:
            print("⚠️ Error conexión:", e)
            time.sleep(10)

def esperar_cierre_vela():
    while True:
        segundos = int(time.time()) % 60
        if segundos == 59:
            time.sleep(1)
            break
        time.sleep(0.2)

def obtener_velas(iq):
    return iq.get_candles(PAR, 60, 100, time.time())

def ejecutar_operacion(iq, direccion):
    print(f"⚡ Ejecutando {direccion.upper()}")

    check, id = iq.buy(MONTO, PAR, direccion, TIEMPO)

    if check:
        print("✅ Operación abierta")
        enviar_telegram(f"📊 {direccion.upper()} ejecutado")

        while True:
            resultado = iq.check_win_v4(id)
            if resultado is not None:
                if resultado > 0:
                    enviar_telegram(f"✅ WIN {resultado}")
                else:
                    enviar_telegram(f"❌ LOSS {resultado}")
                break
            time.sleep(1)
    else:
        print("❌ Error al ejecutar")

# ================= MAIN =================

iq = conectar()

while True:
    try:
        esperar_cierre_vela()

        velas = obtener_velas(iq)

        señal = detectar_entrada(velas)

        if señal:
            ejecutar_operacion(iq, señal)

    except Exception as e:
        print("⚠️ ERROR LOOP:", e)
        iq = conectar()
