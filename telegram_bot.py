import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = telebot.TeleBot(TOKEN)

cambiar_cuenta_func = None
cambiar_monto_func = None


def send_message(msg):
    try:
        bot.send_message(CHAT_ID, msg)
    except:
        pass


def start_telegram(cuenta_func, monto_func):
    global cambiar_cuenta_func, cambiar_monto_func

    cambiar_cuenta_func = cuenta_func
    cambiar_monto_func = monto_func

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("🟢 DEMO"),
        KeyboardButton("🔴 REAL"),
        KeyboardButton("💰 MONTO")
    )

    @bot.message_handler(func=lambda m: True)
    def handle(msg):

        text = msg.text

        if text == "🟢 DEMO":
            cambiar_cuenta_func("PRACTICE")

        elif text == "🔴 REAL":
            cambiar_cuenta_func("REAL")

        elif text == "💰 MONTO":
            bot.send_message(CHAT_ID, "Escribe nuevo monto:")

        elif text.replace(".", "").isdigit():
            cambiar_monto_func(text)

    bot.polling(none_stop=True)
