from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from app.models.database import (
    guardar_mensaje, 
    obtener_contexto_usuario, 
    registrar_verificacion_usuario,  
    verificar_acceso_activo        
)

from app.services.chatbot_users_api import obtener_telefonos_autorizados

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boton_verificar = KeyboardButton(text="📱 Compartir mi número para verificar", request_contact=True)
    
    teclado = ReplyKeyboardMarkup(
        [[boton_verificar]], 
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    mensaje_bienvenida = (
        "¡Hola! Soy tu Pepe, tu ayudante en los datos de tu negocio.\n\n"
        "Para poder ayudarte, primero necesito verificar que tu número "
        "esté autorizado en el sistema."
    )
    
    await update.message.reply_text(mensaje_bienvenida, reply_markup=teclado)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Este handler recibe el número de teléfono de Telegram"""
    telegram_id = update.effective_user.id
    contacto = update.message.contact

    tel_usuario = contacto.phone_number.replace("+", "").strip()

    telefonos_permitidos = obtener_telefonos_autorizados()

    telefonos_limpios = [str(n).replace("+", "").strip() for n in telefonos_permitidos]

    if tel_usuario in telefonos_limpios:
        registrar_verificacion_usuario(telegram_id, tel_usuario)
        await update.message.reply_text("Acceso concedido, Ya puedes hacerme consultas por 24 horas.")
    else:
        await update.message.reply_text("Tu número no tiene permisos en el sistema. Contacta a tu administrador.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    
    if not verificar_acceso_activo(telegram_id):
        await update.message.reply_text("Tu sesión expiró o no te has verificado. Usa /start para renovar tu acceso.")
        return

    texto_usuario = update.message.text
    guardar_mensaje(telegram_id, rol="user", contenido=texto_usuario)
    
    contexto_historico = obtener_contexto_usuario(telegram_id, limite=10)
    
    # Logica Ollama
    respuesta_ia = "Entendido, estoy procesando tu solicitud..." 
    
    guardar_mensaje(telegram_id, rol="assistant", contenido=respuesta_ia)
    await update.message.reply_text(respuesta_ia)

