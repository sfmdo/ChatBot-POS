from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import ContextTypes
from app.ai.agent_orchestrator import query_ai
import textwrap
from app.models.database import (
    save_message, 
    get_user_context, 
    verify_and_register_user,  
    verify_active_access        
)
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

    # 1. Validación de acceso
    if not await verify_active_access(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start.")
        return

    if not user_text:
        await update.message.reply_text("No se ha recibido ningún texto.")
        return

    # 2. Mensaje inicial de "Pepe está pensando..."
    temp_message = await update.message.reply_text("⏳ Pepe está iniciando su análisis...")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    last_status = ""
    final_response = ""

    try:
        # 3. Consumir el generador asíncrono de query_ai
        async for chunk in query_ai(user_text, telegram_id):
            # Si el chunk empieza con 💭 o 🔍 es un estado intermedio
            if chunk.startswith("💭") or chunk.startswith("🔍"):
                # Solo editamos si el estado cambió para evitar spam a la API de Telegram
                if chunk != last_status:
                    try:
                        await temp_message.edit_text(chunk, parse_mode='Markdown')
                        last_status = chunk
                    except BadRequest as e:
                        if "not modified" not in str(e).lower():
                            logger.error(f"Error editando estado: {e}")
            else:
                # Si no tiene esos prefijos, es la RESPUESTA FINAL
                final_response = chunk

        # 4. Enviar la respuesta final
        if final_response:
            try:
                # Intentamos editar el mensaje temporal con la respuesta final
                await temp_message.edit_text(final_response, parse_mode='Markdown')
            except BadRequest as e:
                error_msg = str(e).lower()
                
                # Manejo de mensajes muy largos
                if "message is too long" in error_msg:
                    logger.warning("Respuesta final demasiado larga. Dividiendo...")
                    fragments = split_long_message(final_response)
                    # Editamos el primero
                    await temp_message.edit_text(fragments[0], parse_mode='Markdown')
                    # Enviamos el resto como mensajes nuevos
                    for fragment in fragments[1:]:
                        await update.message.reply_text(fragment, parse_mode='Markdown')
                
                elif "can't parse entities" in error_msg:
                    # Si el Markdown falla, enviamos como texto plano
                    await temp_message.edit_text(final_response)
                
                elif "message is not modified" in error_msg:
                    pass
                else:
                    raise e

    except Exception as e:
        logger.error(f"Error crítico en el flujo de Pepe: {e}")
        try:
            await temp_message.edit_text("❌ Lo siento, Pepe tuvo un error interno al procesar tu solicitud.")
        except:
            await update.message.reply_text("❌ Ocurrió un error crítico.")

    