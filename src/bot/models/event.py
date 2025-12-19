from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Event(SQLModel, table=True):
    """
    Representa um evento agendado no servidor.
    """
    __tablename__ = "events"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    channel_id: int = Field(sa_column=Column(BigInteger))
    message_id: int = Field(sa_column=Column(BigInteger, unique=True)) # ID da mensagem do painel
    organizer_id: int = Field(sa_column=Column(BigInteger))
    
    title: str = Field(description="Título do evento")
    description: str = Field(description="Descrição detalhada")
    start_time: datetime = Field(description="Data e hora de início")
    
    active: bool = Field(default=True)

class EventParticipant(SQLModel, table=True):
    """
    Regista quem vai participar no evento.
    """
    __tablename__ = "event_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    event_id: int = Field(foreign_key="events.id")
    user_id: int = Field(sa_column=Column(BigInteger))
    status: str = Field(default="going") # going (Vou), maybe (Talvez)