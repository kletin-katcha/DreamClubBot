from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class ReactionRole(SQLModel, table=True):
    """
    Mapeia uma reação numa mensagem específica a um cargo.
    """
    __tablename__ = "reaction_roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger))
    channel_id: int = Field(sa_column=Column(BigInteger))
    message_id: int = Field(sa_column=Column(BigInteger))
    
    emoji: str = Field(description="O emoji que dispara a ação (Unicode ou ID)")
    role_id: int = Field(sa_column=Column(BigInteger))