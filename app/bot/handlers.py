from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest, Forbidden, TelegramError
from telegram.ext import ContextTypes
from app.services.ia_service import query_ai
from app.models.database import (
    save_message, 
    get_user_context, 
    register_user_verification,  
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

    allowed_phones = get_authorized_phones()

    cleaned_phones = [str(n).replace("+", "").strip() for n in allowed_phones]

    if user_phone in cleaned_phones:
        register_user_verification(telegram_id, user_phone)
        await update.message.reply_text("Acceso concedido, Ya puedes hacerme consultas por 24 horas.")
    else:
        await update.message.reply_text("Tu número no tiene permisos en el sistema. Contacta a tu administrador.")

def split_long_message(text: str, chunk_size: int = 4000) -> list[str]:
    """
    Divide un texto largo en una lista de fragmentos más pequeños.
    Usamos 4000 en lugar de 4096 para dejar un margen de seguridad.
    """
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    if not verify_active_access(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start para renovar tu acceso.")
        return

    temp_message = await update.message.reply_text("Pepe esta pensando, dale un momento...")

    user_text = update.message.text
    
    if user_text is None:
        ai_response = "No se ha recibido ningun texto del usuario"
        await temp_message.edit_text(ai_response)
    else:
        ai_response = query_ai(user_text, telegram_id)
    
        try:
            await temp_message.edit_text(ai_response) 

        except BadRequest as e:
            error_msg = str(e).lower()

            if "Message_too_long" in error_msg:
                logger.warning("La respuesta de la IA fue muy larga. Dividiendo en fragmentos...")
                fragments = split_long_message(ai_response)
                
                await temp_message.edit_text(fragments[0])

                for fragment in fragments[1:]:
                    await update.message.reply_text(fragment)
                    
            elif "not modified" in error_msg:
                pass
            else:
                logger.error(f"Error BadRequest de Telegram: {e}")
                await temp_message.edit_text("Pepe tuvo un problema de formato al enviar este mensaje.")

        except Forbidden:
            logger.warning(f"El usuario {telegram_id} bloqueó al bot. No se pudo enviar el mensaje.")

        except TelegramError as e:
            logger.error(f"Fallo de conexión con Telegram: {e}")
            await temp_message.edit_text("Pepe está teniendo problemas de señal.")

        except Exception as e:
            logger.error(f"Error interno: {e}")
            await temp_message.edit_text("Ups, a Pepe le dio un dolor de cabeza (Error interno).")

    