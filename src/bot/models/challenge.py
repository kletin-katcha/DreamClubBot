from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import BigInteger, Column

class Challenge(SQLModel, table=True):
    """
    Representa um desafio global criado por administradores.
    """
    __tablename__ = "challenges"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(description="Título do desafio")
    description: str = Field(description="O que deve ser feito")
    xp_reward: int = Field(default=200, description="XP ganho ao completar")
    active: bool = Field(default=True, description="Se o desafio ainda está valendo")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChallengeCompletion(SQLModel, table=True):
    """
    Regista quais utilizadores completaram quais desafios.
    """
    __tablename__ = "challenge_completions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    challenge_id: int = Field(foreign_key="challenges.id")
    user_id: int = Field(sa_column=Column(BigInteger))
    
    completed_at: datetime = Field(default_factory=datetime.utcnow)