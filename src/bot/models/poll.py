from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Poll(SQLModel, table=True):
    """
    Representa uma enquete ativa no servidor.
    """
    __tablename__ = "polls"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    channel_id: int = Field(sa_column=Column(BigInteger))
    message_id: int = Field(sa_column=Column(BigInteger, unique=True)) # ID da mensagem da enquete
    author_id: int = Field(sa_column=Column(BigInteger))
    
    question: str = Field(description="A pergunta da enquete")
    options: str = Field(description="Opções separadas por |") # Ex: "Opção A|Opção B|Opção C"
    
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)