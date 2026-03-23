import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LAST_UPDATE_ID = 0
LAST_COMMAND = None


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": text
        }
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Error Telegram:", e)


def send_buttons(text, buttons):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        keyboard = [[{"text": b}] for b in buttons]

        payload = {
            "chat_id": CHAT_ID,
            "text": text,
            "reply_markup": {
                "keyboard": keyboard,
                "resize_keyboard": True
            }
        }

        requests.post(url, json=payload, timeout=5)

    except Exception as e:
        print("Error botones:", e)


def get_last_command():
    global LAST_COMMAND
    cmd = LAST_COMMAND
    LAST_COMMAND = None
    return cmd


def check_commands():
    global LAST_UPDATE_ID, LAST_COMMAND

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={LAST_UPDATE_ID+1}&timeout=5"
        response = requests.get(url, timeout=10).json()

        if not response.get("result"):
            return

        for update in response["result"]:
            LAST_UPDATE_ID = update["update_id"]

            if "message" in update and "text" in update["message"]:
                LAST_COMMAND = update["message"]["text"]

    except Exception as e:
        print("Error comandos:", e)
