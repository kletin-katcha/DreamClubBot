from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column, Text

class JournalEntry(SQLModel, table=True):
    """
    Representa uma entrada no diário pessoal do usuário.
    Armazena reflexões, pensamentos e aprendizados.
    """
    __tablename__ = "journal_entries"

    id: int | None = Field(default=None, primary_key=True)
    # ID do usuário (BigInteger para compatibilidade com Discord)
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    
    # Usamos Text do SQLAlchemy para permitir textos longos sem limite de 255 chars
    content: str = Field(sa_column=Column(Text)) 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)