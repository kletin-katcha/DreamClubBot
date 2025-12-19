from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class UserSkill(SQLModel, table=True):
    """
    Representa uma habilidade ou interesse profissional.
    Ex: #Python, #Marketing, #Fitness
    """
    __tablename__ = "user_skills"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # ID do usuário dono da habilidade
    user_id: int = Field(sa_column=Column(BigInteger, index=True))
    
    # Nome da habilidade (armazenado em minúsculas para facilitar busca)
    skill: str = Field(index=True, description="Nome da habilidade")