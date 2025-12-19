from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from bot.config import settings
import logging
from contextlib import asynccontextmanager # <--- Importante

logger = logging.getLogger(__name__)

# Configuração da Engine
engine = create_async_engine(
    settings.db_url,
    echo=False, 
    future=True
)

# Fábrica de Sessões
async_session_maker = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def init_db():
    """
    Cria as tabelas no banco de dados se elas não existirem.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Banco de dados inicializado e tabelas verificadas.")
    except Exception as e:
        logger.critical(f"Erro ao inicializar o banco de dados: {e}")
        raise e

@asynccontextmanager # <--- ESTE DECORADOR É OBRIGATÓRIO
async def get_session() -> AsyncSession:
    """
    Gerador assíncrono para fornecer uma sessão de banco de dados.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Erro na sessão do banco: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()