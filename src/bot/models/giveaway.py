from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Giveaway(SQLModel, table=True):
    """
    Representa um sorteio ativo ou finalizado.
    """
    __tablename__ = "giveaways"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    channel_id: int = Field(sa_column=Column(BigInteger))
    message_id: int = Field(sa_column=Column(BigInteger, unique=True)) # ID da mensagem do sorteio
    
    prize: str = Field(description="O prémio a ser sorteado")
    winners_count: int = Field(default=1, description="Número de vencedores")
    
    end_time: datetime = Field(description="Data/Hora de término")
    active: bool = Field(default=True)