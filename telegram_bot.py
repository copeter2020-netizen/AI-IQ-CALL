import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

LAST_UPDATE_ID = 0
BOT_RUNNING = True


def send_message(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": text}
        requests.post(url, data=data, timeout=5)
    except:
        pass


def check_commands():
    global LAST_UPDATE_ID, BOT_RUNNING

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={LAST_UPDATE_ID + 1}"
        response = requests.get(url, timeout=5).json()

        if "result" not in response:
            return BOT_RUNNING

        for update in response["result"]:
            LAST_UPDATE_ID = update["update_id"]

            if "message" not in update:
                continue

            text = update["message"].get("text", "")

            if text == "/start":
                BOT_RUNNING = True
                send_message("🟢 BOT ACTIVADO")

            elif text == "/stop":
                BOT_RUNNING = False
                send_message("🔴 BOT DETENIDO")

    except Exception as e:
        print("Error Telegram:", e)

    return BOT_RUNNING
