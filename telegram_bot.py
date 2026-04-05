import time
import threading
from telegram import Bot
from telegram.ext import Updater, CommandHandler
from estrategia import detectar_entrada_oculta

TOKEN = "TU_TOKEN_AQUI"
CHAT_ID = "TU_CHAT_ID"

bot = Bot(token=TOKEN)

bot_activo = False


# ==========================
# COMANDOS
# ==========================
def startbot(update, context):
    global bot_activo
    bot_activo = True
    update.message.reply_text("✅ Bot ACTIVADO")


def stopbot(update, context):
    global bot_activo
    bot_activo = False
    update.message.reply_text("🛑 Bot DETENIDO")


# ==========================
# LOOP DEL BOT
# ==========================
def ejecutar_bot():

    global bot_activo

    while True:

        if bot_activo:
            try:
                # 🔴 AQUÍ debes conectar tu data real
                data = obtener_datos()  # <-- debes tener esta función

                señal = detectar_entrada_oculta(data)

                if señal:
                    par, direccion, score = señal

                    mensaje = f"""
🔥 SEÑAL DETECTADA 🔥

Par: {par}
Dirección: {direccion.upper()}
Score: {score}
"""
                    bot.send_message(chat_id=CHAT_ID, text=mensaje)

            except Exception as e:
                print("Error:", e)

        time.sleep(10)


# ==========================
# MAIN
# ==========================
def main():

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("startbot", startbot))
    dp.add_handler(CommandHandler("stopbot", stopbot))

    hilo = threading.Thread(target=ejecutar_bot)
    hilo.start()

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
