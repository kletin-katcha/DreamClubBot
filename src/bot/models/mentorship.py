from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Mentorship(SQLModel, table=True):
    """
    Relacionamento de Mentoria.
    Um Mentor guia um Aprendiz.
    """
    __tablename__ = "mentorships"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    mentor_id: int = Field(sa_column=Column(BigInteger, index=True))
    apprentice_id: int = Field(sa_column=Column(BigInteger, unique=True)) # Um aprendiz só tem 1 mentor
    
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)