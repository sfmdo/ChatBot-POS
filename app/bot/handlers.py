from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from app.ai.agent_orchestrator import query_ai
import textwrap
from app.models.database import (
    verify_and_register_user,  
    verify_active_access        
)
from split_text import split_long_message
import logging

logger = logging.getLogger(__name__)

from app.services.chatbot_users_api import get_authorized_phones

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    verify_button = KeyboardButton(text="📱 Compartir mi número para verificar", request_contact=True)
    
    keyboard = ReplyKeyboardMarkup(
        [[verify_button]], 
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    welcome_message = (
        "¡Hola! Soy tu Pepe, tu ayudante en los datos de tu negocio.\n\n"
        "Para poder ayudarte, primero necesito verificar que tu número "
        "esté autorizado en el sistema."
    )
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This handler receives the Telegram phone number"""
    telegram_id = update.effective_user.id
    contact = update.message.contact

    user_phone = contact.phone_number.replace("+", "").strip()

    allowed_phones = await get_authorized_phones()

    cleaned_phones = [str(n).replace("+", "").strip() for n in allowed_phones]

    if user_phone in cleaned_phones:
        await verify_and_register_user(telegram_id, user_phone)
        await update.message.reply_text("Acceso concedido, Ya puedes hacerme consultas por 24 horas.")
    else:
        await update.message.reply_text("Tu número no tiene permisos en el sistema. Contacta a tu administrador.")


def split_long_message(text, limit=4000):
    return textwrap.wrap(text, limit, break_long_words=False, replace_whitespace=False)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    user_text = update.message.text

    if not await verify_active_access(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start.")
        return

    temp_message = await update.message.reply_text("⏳ Pepe está iniciando su análisis...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    last_status = ""
    final_response = ""

    try:
        async for chunk in query_ai(user_text, telegram_id):
            # 1. Manejo de estados intermedios (Pensamientos)
            if chunk.startswith("🧠") or chunk.startswith("📋") or chunk.startswith("💡"):
                if chunk != last_status:
                    try:
                        # Cortamos el estado si por alguna razón fuera muy largo (raro en pensamientos)
                        display_status = chunk[:4000]
                        await temp_message.edit_text(display_status, parse_mode='Markdown')
                        last_status = chunk
                    except BadRequest as e:
                        if "not modified" not in str(e).lower():
                            logger.error(f"Error editando estado: {e}")
            else:
                # Acumular o identificar la respuesta final
                final_response = chunk

        # 2. Envío de la Respuesta Final (Proactivo)
        if final_response:
            fragments = split_long_message(final_response)
            
            for i, fragment in enumerate(fragments):
                try:
                    if i == 0:
                        # El primer fragmento edita el mensaje de "Pepe está pensando..."
                        await temp_message.edit_text(fragment, parse_mode='Markdown')
                    else:
                        # Los siguientes fragmentos se envían como mensajes nuevos
                        await update.message.reply_text(fragment, parse_mode='Markdown')
                
                except BadRequest as e:
                    # Si falla el Markdown (por fragmentos que cortaron etiquetas), reintentar sin Markdown
                    if "can't parse entities" in str(e).lower():
                        if i == 0:
                            await temp_message.edit_text(fragment)
                        else:
                            await update.message.reply_text(fragment)
                    else:
                        logger.error(f"Error enviando fragmento {i}: {e}")

    except Exception as e:
        logger.error(f"Error crítico en el flujo de Pepe: {e}")
        try:
            await temp_message.edit_text("❌ Lo siento, Pepe tuvo un error interno al procesar tu solicitud.")
        except:
            pass

    