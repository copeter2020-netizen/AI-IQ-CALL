import time
import requests
from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================
EMAIL = "TU_EMAIL"
PASSWORD = "TU_PASSWORD"

TELEGRAM_TOKEN = "TU_TOKEN_BOT"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

PARES = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC"
]

TIEMPO = 60
MONTO = 2
# ==========================================


# ===== TELEGRAM =====
def enviar_telegram(mensaje):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensaje
        }
        requests.post(url, data=data)
    except Exception as e:
        print("Error Telegram:", e)


# ===== CONEXIÓN =====
def conectar():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    if iq.check_connect():
        print("✅ Conectado a IQ Option")
        enviar_telegram("🤖 Bot conectado correctamente")
        return iq
    else:
        print("❌ Error conexión")
        enviar_telegram("❌ Error de conexión a IQ Option")
        return None


# ===== OBTENER VELAS =====
def obtener_velas(iq, par):
    velas = iq.get_candles(par, 60, 50, time.time())
    return velas


# ===== SOPORTE / RESISTENCIA =====
def zonas(velas):
    maximo = max([v['max'] for v in velas])
    minimo = min([v['min'] for v in velas])
    return maximo, minimo


# ===== DETECTAR ENTRADA =====
def detectar_entrada(velas):
    ultima = velas[-1]
    anterior = velas[-2]

    cierre = ultima['close']
    apertura = ultima['open']

    cuerpo = abs(cierre - apertura)

    direccion = None

    # tendencia simple
    if cierre > apertura:
        direccion = "CALL"
    elif cierre < apertura:
        direccion = "PUT"

    # fuerza de vela
    if cuerpo < 0.00005:
        return None

    return direccion


# ===== FILTRO IA =====
def filtro_ia(velas):
    maximo, minimo = zonas(velas)
    precio = velas[-1]['close']

    rango = maximo - minimo

    # evitar rango lateral
    if rango < 0.0003:
        return False

    # evitar centro del rango
    if minimo + (rango * 0.4) < precio < minimo + (rango * 0.6):
        return False

    return True


# ===== ENTRADA EXACTA =====
def esperar_cierre():
    while True:
        segundos = int(time.time()) % 60

        # entrar 1 segundo antes del cierre
        if segundos == 58:
            return
        time.sleep(0.5)


# ===== EJECUTAR TRADE =====
def ejecutar_trade(iq, par, direccion):
    try:
        status, id = iq.buy(MONTO, par, direccion, 1)

        if status:
            print(f"✅ {par} -> {direccion}")

            enviar_telegram(
                f"📊 SEÑAL\n"
                f"Par: {par}\n"
                f"Dirección: {direccion}\n"
                f"Tiempo: 1 min\n"
                f"Monto: ${MONTO}"
            )
        else:
            print("❌ Error operación")

    except Exception as e:
        print("Error trade:", e)


# ===== LOOP PRINCIPAL =====
def main():
    iq = conectar()

    if iq is None:
        return

    while True:
        try:
            for par in PARES:

                velas = obtener_velas(iq, par)

                if not velas:
                    continue

                # FILTRO IA
                if not filtro_ia(velas):
                    continue

                # DETECCIÓN
                direccion = detectar_entrada(velas)

                if direccion is None:
                    continue

                # ESPERAR CIERRE
                esperar_cierre()

                # EJECUTAR
                ejecutar_trade(iq, par, direccion)

                time.sleep(2)

        except Exception as e:
            print("ERROR LOOP:", e)
            time.sleep(5)


# ===== RUN =====
if __name__ == "__main__":
    main()
