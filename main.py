import logging
from dotenv import load_dotenv
load_dotenv()
from app.bot.client import application

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    logger.info("Iniciando el Agente POS en Telegram...")
    
    application.run_polling()

if __name__ == "__main__":
    main()