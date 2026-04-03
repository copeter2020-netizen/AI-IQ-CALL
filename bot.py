import time
import os
from iqoptionapi.stable_api import IQ_Option
from strategy import detectar_entrada

EMAIL = os.getenv("IQ_EMAIL")
PASSWORD = os.getenv("IQ_PASSWORD")

PARES = [
    "EURUSD-OTC",
    "EURGBP-OTC",
    "EURJPY-OTC",
    "GBPUSD-OTC",
    "GBPJPY-OTC"
]

MONTO = 8
EXPIRACION = 1

bloqueo_hasta = 0


def conectar():
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()

    if iq.check_connect():
        iq.change_balance("PRACTICE")
        return iq
    return None


def esperar_sniper():
    while True:
        seg = time.time() % 60
        if 58.98 <= seg <= 59.2:
            return
        time.sleep(0.002)


def validar_triple(iq, par):
    señales = []

    for _ in range(3):
        velas = iq.get_candles(par, 60, 150, time.time())

        if isinstance(velas, tuple):
            velas = velas[1]

        señales.append(detectar_entrada(velas))
        time.sleep(0.3)

    if señales.count(señales[0]) == len(señales):
        return señales[0]

    return None


def run():
    global bloqueo_hasta

    iq = conectar()
    if iq is None:
        return

    while True:
        try:
            if time.time() < bloqueo_hasta:
                time.sleep(10)
                continue

            for par in PARES:

                señal = validar_triple(iq, par)

                if señal:

                    print(f"🧠 SETUP REPETIBLE {par} → {señal}")

                    esperar_sniper()

                    status, trade_id = iq.buy(MONTO, par, señal, EXPIRACION)

                    if status:
                        while True:
                            resultado = iq.check_win_v4(trade_id)

                            if resultado is not None:
                                if resultado <= 0:
                                    print("❌ LOSS → BLOQUEO")
                                    bloqueo_hasta = time.time() + 3600
                                else:
                                    print("✅ WIN")
                                break

                            time.sleep(1)

                    break

            time.sleep(1)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(3)


if __name__ == "__main__":
    run()
