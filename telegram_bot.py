import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot_activo = False
last_update = 0


def enviar(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass


def escuchar():
    global bot_activo, last_update

    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update + 1}",
            timeout=5
        ).json()

        for update in r.get("result", []):
            last_update = update["update_id"]

            msg = update.get("message", {}).get("text", "")

            if msg == "/startbot":
                bot_activo = True
                enviar("✅ BOT ACTIVADO")

            elif msg == "/stopbot":
                bot_activo = False
                enviar("⛔ BOT DETENIDO")

    except:
        pass

    return bot_activo
