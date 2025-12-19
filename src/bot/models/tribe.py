from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Tribe(SQLModel, table=True):
    """
    Representa um grupo de utilizadores (Tribo/Clã).
    """
    __tablename__ = "tribes"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, description="Nome da Tribo")
    description: str = Field(default="Uma tribo focada em evolução.", description="Lema ou descrição")
    
    # ID do Líder (BigInteger)
    leader_id: int = Field(sa_column=Column(BigInteger))
    
    # Pontuação da Tribo (pode ser usada em rankings futuros)
    score: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TribeMember(SQLModel, table=True):
    """
    Tabela de associação: Liga um Utilizador a uma Tribo.
    """
    __tablename__ = "tribe_members"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    tribe_id: int = Field(foreign_key="tribes.id")
    user_id: int = Field(sa_column=Column(BigInteger, unique=True)) # Um user só pode ter 1 tribo
    
    joined_at: datetime = Field(default_factory=datetime.utcnow)