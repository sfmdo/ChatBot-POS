import os

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.bot.handlers import start_command, handle_message, handle_contact, help_command, tutorial_command

token = os.getenv('TELEGRAM_TOKEN')

if not token:
    raise ValueError("No se encontró el token de telegram en el archivo .env")

application = ApplicationBuilder().token(token).build()

application.add_handler(CommandHandler("start", start_command))
application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("tutorial", tutorial_command))
