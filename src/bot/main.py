import asyncio
import logging
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bot.config import settings
from bot.client import DreamClubBot 
from bot.utils.logger import setup_logger

async def main():
    setup_logger()
    logger = logging.getLogger("Launcher")
    
    # Valida Token
    token = settings.current_token
    if not token:
        logger.critical(f"Token não encontrado para o perfil {settings.bot_profile}!")
        logger.critical("Verifique seu arquivo .env")
        return

    logger.info(f"Iniciando perfil: {settings.bot_profile}")

    bot = DreamClubBot()

    async with bot:
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            logger.info("Desligando...")
        except Exception as e:
            logger.critical(f"Falha catastrófica: {e}")

if __name__ == "__main__":
    if sys.platform != "win32":
        try:
            import uvloop
            uvloop.install()
        except ImportError: pass

    try:
        asyncio.run(main())
    except KeyboardInterrupt: pass