from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class AFKStatus(SQLModel, table=True):
    """
    Armazena o estado de ausência de um membro.
    """
    __tablename__ = "afk_status"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Usamos unique=True porque um usuário só pode ter um status AFK ativo
    user_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    guild_id: int = Field(sa_column=Column(BigInteger))
    
    reason: str = Field(default="Ocupado", description="Motivo da ausência")
    start_time: datetime = Field(default_factory=datetime.utcnow)