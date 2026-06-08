from telegram import Update, ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import ContextTypes
from app.ai.agent_orchestrator import query_ai
import textwrap
from app.models.database import (
    verify_and_register_user,  
    verify_active_access        
)
from app.bot.split_text import split_long_message
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
        "\nUna vez registrado, puedes utilizar el comando /help para guiarte y ver los recursos disponibles"
    )
    
    await update.message.reply_text(welcome_message, reply_markup=keyboard) # type: ignore

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """This handler receives the Telegram phone number"""
    telegram_id = update.effective_user.id # type: ignore
    contact = update.message.contact # type: ignore

    user_phone = contact.phone_number.replace("+", "").strip() # type: ignore

    allowed_phones = await get_authorized_phones()

    cleaned_phones = [str(n).replace("+", "").strip() for n in allowed_phones]

    if user_phone in cleaned_phones:
        await verify_and_register_user(telegram_id, user_phone)
        await update.message.reply_text("Acceso concedido, Ya puedes hacerme consultas por 24 horas.") # type: ignore
    else:
        await update.message.reply_text("Tu número no tiene permisos en el sistema. Contacta a tu administrador.") # type: ignore


def split_long_message(text, limit=4000):
    return textwrap.wrap(text, limit, break_long_words=False, replace_whitespace=False)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id # type: ignore
    user_text = update.message.text # type: ignore

    if not await verify_active_access(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start.") # type: ignore
        return

    temp_message = await update.message.reply_text("⏳ Pepe está iniciando su análisis...") # type: ignore
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing') # type: ignore

    last_status = ""
    final_response = ""

    try:
        async for chunk in query_ai(user_text, telegram_id): # type: ignore
            if chunk.startswith("🧠") or chunk.startswith("📋") or chunk.startswith("💡"):
                if chunk != last_status:
                    try:
                        display_status = chunk[:4000]
                        await temp_message.edit_text(display_status, parse_mode='Markdown')
                        last_status = chunk
                    except BadRequest as e:
                        if "not modified" not in str(e).lower():
                            logger.error(f"Error editando estado: {e}")
            else:
                final_response = chunk

        if final_response:
            fragments = split_long_message(final_response)
            
            for i, fragment in enumerate(fragments):
                try:
                    if i == 0:
                        await temp_message.edit_text(fragment, parse_mode='Markdown')
                    else:
                        await update.message.reply_text(fragment, parse_mode='Markdown') # type: ignore
                
                except BadRequest as e:

                    if "can't parse entities" in str(e).lower():
                        if i == 0:
                            await temp_message.edit_text(fragment)
                        else:
                            await update.message.reply_text(fragment) # type: ignore
                    else:
                        logger.error(f"Error enviando fragmento {i}: {e}")

    except Exception as e:
        logger.error(f"Error crítico en el flujo de Pepe: {e}")
        try:
            await temp_message.edit_text("Lo siento, Pepe tuvo un error interno al procesar tu solicitud.")
        except:
            pass

async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ejemplos generales por categoría."""
    tutorial_text = (
        "💡 *Guía de Consulta Pepe*\n"
        "IMPORTANTE: Recuerda siempre especificar a que se refiere cada elemento de tu peticion, si es un producto, cliente, etc.\n\n"
        "Puedes preguntarme sobre estos temas de forma general:\n\n"
        "💰 *Análisis de Ventas*\n"
        "• Resúmenes de ingresos por periodos (día, semana, mes, año).\n"
        "• Comparativas de rendimiento entre fechas.\n"
        "• Análisis de horas pico y momentos de más flujo.\n"
        "• Ranking de productos más y menos vendidos.\n\n"
        "📦 *Gestión de Inventario*\n"
        "• Consultas de precios y existencias actuales.\n"
        "• Reportes de productos que están por agotarse.\n"
        "• Valoración monetaria de lo que tienes en bodega.\n"
        "• Identificación de productos que no se están vendiendo.\n\n"
        "🤝 *Clientes y Créditos*\n"
        "• Búsqueda de perfiles y hábitos de compra.\n"
        "• Seguimiento de deudas y estados de cuenta.\n"
        "• Listado de clientes frecuentes o por fechas especiales.\n\n"
        "🚛 *Proveedores*\n"
        "• Información fiscal y de contacto.\n"
        "• Catálogo de productos por cada proveedor.\n\n"
        "👉 *Escribe ahora:* _'¿Qué productos se están agotando?'_ o _'Resumen de este mes'_"
    )

    if update.message:
        await update.message.reply_text(tutorial_text, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.message.reply_text(tutorial_text, parse_mode='Markdown') # type: ignore

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explica qué es Pepe y cómo interactuar."""
    help_text = (
        "*¿Quién es Pepe?*\n"
        "Soy tu Analista de Inteligencia de Negocios. No soy un chat común; tengo acceso directo a tu punto de venta para procesar datos y darte conclusiones útiles.\n\n"
        "*Comandos Principales:*\n"
        "🚀 /start - Iniciar o verificar tu acceso.\n"
        "📖 /tutorial - Guía de cómo hacerme preguntas.\n"
        "❓ /help - Ver este mensaje.\n\n"
        "*Reglas de oro para hablar conmigo:*\n"
        "1️⃣ *Habla natural:* No necesitas códigos, dime: _'¿Cómo fueron las ventas de ayer?'_\n"
        "2️⃣ *Sé específico con el tiempo:* Usa frases como _'este mes'_, _'la semana pasada'_ o fechas exactas.\n"
        "3️⃣ *Pide consejos:* Puedes preguntarme _'¿Qué me recomiendas hacer?'_ después de un reporte."
    )
    
    keyboard = [[InlineKeyboardButton("📖 Ver ejemplos generales", callback_data="show_tutorial")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=reply_markup) # type: ignore