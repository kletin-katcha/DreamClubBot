from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Tag(SQLModel, table=True):
    """
    Representa um comando de texto personalizado (Tag).
    """
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger, index=True))
    author_id: int = Field(sa_column=Column(BigInteger))
    
    name: str = Field(index=True, description="Nome do gatilho (sem espaços)")
    content: str = Field(description="Texto que o bot vai responder")
    
    uses: int = Field(default=0, description="Quantas vezes foi usada")
    created_at: datetime = Field(default_factory=datetime.utcnow)