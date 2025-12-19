from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class StarboardConfig(SQLModel, table=True):
    """Configuração do Starboard por servidor."""
    __tablename__ = "starboard_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    channel_id: int = Field(sa_column=Column(BigInteger)) # Onde as mensagens vão aparecer
    threshold: int = Field(default=3) # Mínimo de estrelas para aparecer

class StarboardEntry(SQLModel, table=True):
    """Rastreio de mensagens que já estão no quadro."""
    __tablename__ = "starboard_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    original_message_id: int = Field(sa_column=Column(BigInteger, unique=True))
    starboard_message_id: int = Field(sa_column=Column(BigInteger)) # ID da mensagem enviada pelo bot
    channel_id: int = Field(sa_column=Column(BigInteger)) # Canal original
    stars: int = Field(default=0)