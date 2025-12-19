from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Ticket(SQLModel, table=True):
    """
    Registo de um ticket de suporte.
    """
    __tablename__ = "tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    channel_id: int = Field(sa_column=Column(BigInteger, unique=True)) # ID do canal de texto criado
    user_id: int = Field(sa_column=Column(BigInteger)) # Quem abriu
    
    status: str = Field(default="open") # open, closed
    created_at: datetime = Field(default_factory=datetime.utcnow)