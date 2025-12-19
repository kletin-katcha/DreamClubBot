from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class Birthday(SQLModel, table=True):
    """
    Armazena a data de aniversário dos membros.
    """
    __tablename__ = "birthdays"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    
    day: int = Field(description="Dia do nascimento (1-31)")
    month: int = Field(description="Mês do nascimento (1-12)")