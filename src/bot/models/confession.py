from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Confession(SQLModel, table=True):
    """
    Registo de um desabafo anónimo.
    """
    __tablename__ = "confessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    author_id: int = Field(sa_column=Column(BigInteger)) # Quem enviou (para logs)
    message_id: int = Field(sa_column=Column(BigInteger)) # ID da mensagem enviada no canal
    
    content: str = Field(description="Conteúdo do desabafo")
    created_at: datetime = Field(default_factory=datetime.utcnow)