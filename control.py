import requests
import os

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

estado = True  # True = activo, False = detenido
last_update_id = None


def obtener_comandos():
    global last_update_id, estado

    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
        params = {"timeout": 1}

        if last_update_id:
            params["offset"] = last_update_id + 1

        res = requests.get(url, params=params, timeout=5).json()

        for update in res.get("result", []):
            last_update_id = update["update_id"]

            if "message" in update:
                texto = update["message"].get("text", "").lower()

                if str(update["message"]["chat"]["id"]) != str(CHAT_ID):
                    continue

                if texto == "/on":
                    estado = True
                    enviar("🟢 BOT ACTIVADO")

                elif texto == "/off":
                    estado = False
                    enviar("🔴 BOT DETENIDO")

    except:
        pass

    return estado


def enviar(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg
        }, timeout=5)
    except:
        pass
