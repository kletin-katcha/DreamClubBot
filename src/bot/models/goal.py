from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Goal(SQLModel, table=True):
    """
    Representa uma meta ou objetivo definido pelo usuário.
    """
    __tablename__ = "goals"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Usamos BigInteger novamente para garantir compatibilidade com IDs do Discord
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    
    description: str = Field(description="Descrição do objetivo")
    completed: bool = Field(default=False, description="Status de conclusão")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)