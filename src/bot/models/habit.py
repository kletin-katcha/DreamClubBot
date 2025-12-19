from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Habit(SQLModel, table=True):
    """
    Representa um hábito recorrente (Streak).
    """
    __tablename__ = "habits"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    
    name: str = Field(description="Nome do hábito (ex: Leitura, Treino)")
    
    current_streak: int = Field(default=0, description="Sequência atual de dias")
    longest_streak: int = Field(default=0, description="Melhor sequência registada")
    
    last_checkin: Optional[datetime] = Field(default=None, description="Data do último check-in")
    created_at: datetime = Field(default_factory=datetime.utcnow)