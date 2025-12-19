from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Reminder(SQLModel, table=True):
    """
    Representa um lembrete agendado pelo usuário.
    """
    __tablename__ = "reminders"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    channel_id: int = Field(sa_column=Column(BigInteger)) # Onde avisar (pode ser DM ou canal)
    
    message: str = Field(description="A mensagem do lembrete")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_at: datetime = Field(description="Quando o lembrete deve disparar")
    
    active: bool = Field(default=True)