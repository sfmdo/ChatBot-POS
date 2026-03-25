from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from app.services.ai_service import query_ai
from app.models.database import (
    save_message, 
    get_user_context, 
    register_user_verification,  
    verify_active_access        
)

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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    if not verify_active_access(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start para renovar tu acceso.")
        return

    temp_message = await update.message.reply_text("Consultando tu consulta, dame un momento...")

    user_text = update.message.text
    
    if user_text is None:
        ai_response = "No se ha recibido ningun texto del usuario"
    else:
        ai_response = query_ai(user_text, telegram_id)
    
    await temp_message.edit_text(ai_response)