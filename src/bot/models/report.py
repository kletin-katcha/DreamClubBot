from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Report(SQLModel, table=True):
    """
    Registo de uma denúncia.
    """
    __tablename__ = "reports"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    reporter_id: int = Field(sa_column=Column(BigInteger)) # Quem denunciou
    target_id: int = Field(sa_column=Column(BigInteger))   # Quem foi denunciado
    
    reason: str = Field(description="Motivo da denúncia")
    message_content: Optional[str] = Field(default=None, description="Conteúdo da mensagem reportada (se houver)")
    attachment_url: Optional[str] = Field(default=None, description="Prova visual")
    
    status: str = Field(default="pending") # pending, resolved, dismissed
    created_at: datetime = Field(default_factory=datetime.utcnow)