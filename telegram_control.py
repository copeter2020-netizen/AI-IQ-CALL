from telegram_bot import send_buttons, get_last_command

is_running = True


def init_telegram():
    send_buttons("🤖 Control del BOT", ["▶️ Iniciar", "⛔ Detener", "📊 Estado"])


def process_telegram():
    global is_running

    cmd = get_last_command()

    if not cmd:
        return is_running

    if "Iniciar" in cmd:
        is_running = True
        print("✅ BOT ACTIVADO")

    elif "Detener" in cmd:
        is_running = False
        print("⛔ BOT DETENIDO")

    elif "Estado" in cmd:
        estado = "ACTIVO" if is_running else "DETENIDO"
        print(f"📊 Estado: {estado}")

    return is_running
