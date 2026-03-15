from telegram import Update
from telegram.ext import ContextTypes
from app.models.database import guardar_mensaje, obtener_contexto_usuario

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje_bienvenida = (
        "¡Hola! Soy tu Agente de Punto de Venta (POS) 🤖.\n\n"
        "Puedes preguntarme sobre las ventas del día, inventario, "
        "o cualquier duda sobre tu negocio."
    )
    await update.message.reply_text(mensaje_bienvenida)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.message.from_user.id
    texto_usuario = update.message.text
    
    guardar_mensaje(telegram_id, rol="user", contenido=texto_usuario)
    
    contexto_historico = obtener_contexto_usuario(telegram_id, limite=10)
    
    #Llamar a ollama y mandar contexto

    respuesta_ia = "Entendido, estoy procesando tu solicitud..." 
    
    guardar_mensaje(telegram_id, rol="assistant", contenido=respuesta_ia)
    
    await update.message.reply_text(respuesta_ia)
