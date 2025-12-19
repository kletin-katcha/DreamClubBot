from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Suggestion(SQLModel, table=True):
    """
    Representa uma sugestão enviada por um membro.
    """
    __tablename__ = "suggestions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    author_id: int = Field(sa_column=Column(BigInteger))
    message_id: int = Field(sa_column=Column(BigInteger, unique=True)) # ID da mensagem no canal de sugestões
    
    content: str = Field(description="O conteúdo da sugestão")
    status: str = Field(default="pending") # pending, approved, rejected
    
    created_at: datetime = Field(default_factory=datetime.utcnow)