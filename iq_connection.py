# ==========================
# 🔥 PARCHE GLOBAL (ANTES DE TODO)
# ==========================
try:
    from iqoptionapi import stable_api

    stable_api.IQ_Option._get_digital_open = lambda *a, **k: None
    stable_api.IQ_Option.get_digital_underlying_list_data = lambda self: {"underlying": []}

except:
    pass


# ==========================
# IMPORTS
# ==========================
import os
import time
from iqoptionapi.stable_api import IQ_Option
from telegram_bot import send_message


IQ_EMAIL = os.environ.get("IQ_EMAIL")
IQ_PASSWORD = os.environ.get("IQ_PASSWORD")


# ==========================
# CONEXIÓN
# ==========================
def connect_iq():

    print("🔌 Conectando a IQ Option...")

    iq = IQ_Option(IQ_EMAIL, IQ_PASSWORD)

    # ==========================
    # 🔥 PARCHE ANTES DE CONNECT
    # ==========================
    try:
        iq.api._get_digital_open = lambda *a, **k: None
        iq.api.get_digital_underlying_list_data = lambda: {"underlying": []}
        iq.api.subscribe_digital_underlying = lambda *a, **k: None
        iq.api.unsubscribe_digital_underlying = lambda *a, **k: None
    except:
        pass

    check, reason = iq.connect()

    if check:

        print("✅ Conectado correctamente")
        send_message("🤖 BOT CONECTADO (SIN ERRORES)")

        # ==========================
        # 🔥 PARCHE DESPUÉS DE CONNECT
        # ==========================
        try:
            iq.api._get_digital_open = lambda *a, **k: None
            iq.api.get_digital_open = lambda *a, **k: None

            iq.api.digital_underlying_list_data = {"underlying": []}
            iq.api.get_digital_underlying_list_data = lambda: {"underlying": []}

            iq.api.subscribe_digital_underlying = lambda *a, **k: None
            iq.api.unsubscribe_digital_underlying = lambda *a, **k: None

            iq.api.digital_option = {}
            iq.api.digital_opened = {}

        except Exception as e:
            print("Parche aplicado:", e)

        # ==========================
        # 🔥 SOLO BINARIAS
        # ==========================
        try:
            iq.get_all_open_time()
        except:
            pass

        return iq

    print("❌ Error conectando:", reason)
    send_message("❌ ERROR CONECTANDO")

    time.sleep(5)
    return None
