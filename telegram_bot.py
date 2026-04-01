import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

URL = f"https://api.telegram.org/bot{TOKEN}"

LAST_UPDATE_ID = None


# ==========================
# 📤 MENSAJE TEXTO
# ==========================
def send_message(text):
    try:
        requests.post(
            f"{URL}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": text
            },
            timeout=5
        )
    except:
        pass


# ==========================
# 🖼️ ENVIAR IMAGEN
# ==========================
def send_image(path, caption=""):
    try:
        with open(path, "rb") as photo:
            requests.post(
                f"{URL}/sendPhoto",
                data={
                    "chat_id": CHAT_ID,
                    "caption": caption
                },
                files={"photo": photo},
                timeout=10
            )
    except:
        pass


# ==========================
# 📥 LEER COMANDOS
# ==========================
def get_command():
    global LAST_UPDATE_ID

    try:
        response = requests.get(
            f"{URL}/getUpdates",
            params={"timeout": 5, "offset": LAST_UPDATE_ID},
            timeout=5
        ).json()

        if not response.get("ok"):
            return None

        results = response.get("result", [])

        if not results:
            return None

        last = results[-1]
        LAST_UPDATE_ID = last["update_id"] + 1

        message = last.get("message", {})
        text = message.get("text", "")

        return text

    except:
        return None
