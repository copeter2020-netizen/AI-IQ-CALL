import time
import os
from iqoptionapi.stable_api import IQ_Option
from estrategia import detectar_entrada_oculta

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

MONTO = 508
CUENTA = "PRACTICE"

ultima_entrada = 0


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

                # 🔥 evita bug digital
                try:
                    iq.get_all_open_time()
                except:
                    pass

                print("✅ BOT CONECTADO")
                return iq

        except Exception as e:
            print("Error conexión:", e)

        time.sleep(5)


# =========================
# VALIDAR ACTIVO
# =========================
def activo_abierto(iq, par):
    try:
        data = iq.get_all_open_time()
        return data.get("binary", {}).get(par, {}).get("open", True)
    except:
        return True


# =========================
# TIMING INTELIGENTE
# =========================
def esperar_momento():
    # 🔥 entra en mejor zona sin congelar
    for _ in range(50):
        segundos = int(time.time() % 60)
        if segundos >= 57:
            return
        time.sleep(0.02)


# =========================
# VELAS
# =========================
def obtener_velas(iq, par, timeframe):
    try:
        velas = iq.get_candles(par, timeframe, 50, time.time())
        return velas if velas else None
    except:
        return None


# =========================
# EJECUCIÓN INTELIGENTE
# =========================
def ejecutar_orden(iq, par, direccion):

    # 🔥 intento 1: normal
    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)
        if status:
            return True, order_id
    except:
        pass

    # 🔥 intento 2: invertir timing
    time.sleep(0.3)
    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)
        if status:
            return True, order_id
    except:
        pass

    # 🔥 intento 3: último intento directo
    try:
        status, order_id = iq.buy(MONTO, par, direccion, 1)
        if status:
            return True, order_id
    except:
        pass

    return False, None


# =========================
# OPERAR (CORREGIDO REAL)
# =========================
def operar(iq, par, direccion):
    global ultima_entrada

    if time.time() - ultima_entrada < 8:
        return

    if not activo_abierto(iq, par):
        print(f"❌ {par} cerrado")
        return

    print(f"⏳ Ejecutando {par}...")

    esperar_momento()

    ok, order_id = ejecutar_orden(iq, par, direccion)

    if ok:
        print(f"🚀 {par} {direccion} | ID: {order_id}")
        ultima_entrada = time.time()
    else:
        print("❌ Falló ejecución total")


# =========================
# MAIN (ANTI-CRASH)
# =========================
def run():
    iq = conectar()

    PARES = [
        "EURUSD-OTC",
        "GBPUSD-OTC",
        "USDJPY-OTC",
        "USDCHF-OTC",
        "EURJPY-OTC",
        "GBPJPY-OTC"
    ]

    while True:
        try:
            data = {}

            for par in PARES:
                m1 = obtener_velas(iq, par, 60)
                m5 = obtener_velas(iq, par, 300)

                if m1 and m5:
                    data[par] = {"m1": m1, "m5": m5}

            if not data:
                time.sleep(1)
                continue

            señal = detectar_entrada_oculta(data)

            if señal:
                par, direccion, score = señal

                print(f"""
📊 SEÑAL DETECTADA
{par} {direccion}
Score: {score}
""")

                operar(iq, par, direccion)

            time.sleep(0.3)

        except Exception as e:
            print("Error general:", e)
            time.sleep(2)


if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print("🔥 Reiniciando:", e)
            time.sleep(3)
