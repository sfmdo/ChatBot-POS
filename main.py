import logging
import sys
from dotenv import load_dotenv
load_dotenv()

from app.bot.client import application
from app.models.database import create_tables
from app.src.scripts.process_global_documents import process_global_documents

from agent_mcp.client import mcp_manager

logging.basicConfig(
    stream=sys.stderr, 
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True,
)

logging.getLogger("rag_lite").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

async def post_init_setup(app):
    """
    This function runs INSIDE the bot's event loop before it starts reading messages.
    Here we initialize the database, load RAG documents, and start the MCP server.
    """
    # --- Initialize Database ---
    logger.info("Verifying database tables...")
    await create_tables()
    logger.info("Database ready.")

    # --- Initialize RAG ---
    logger.info("Checking for pending RAG documents...")
    try:
        await process_global_documents()
        logger.info("RAG documents processed successfully.")
    except Exception as e:
        logger.error(f"Error initializing RAG documents: {e}")

    # --- Initialize MCP ---
    logger.info("Starting MCP server in the background with uv...")
    try:
        await mcp_manager.start()
        logger.info("MCP Client connected. Pepe now has access to his tools!")
    except Exception as e:
        logger.error(f"Critical error starting MCP: {e}")

async def post_shutdown_setup(app):
    """
    This function runs when you shut down the bot.
    It ensures the uv/mcp process closes cleanly and doesn't remain as a 'zombie' process.
    """
    logger.info("Shutting down MCP client...")
    try:
        await mcp_manager.stop()
        logger.info("MCP server shut down successfully.")
    except Exception as e:
        logger.error(f"Error shutting down MCP: {e}")

def main():
    logger.info("Configuring POS Agent on Telegram...")
    
    # Assign setup and shutdown functions
    application.post_init = post_init_setup
    application.post_shutdown = post_shutdown_setup

    logger.info("Pepe is starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()