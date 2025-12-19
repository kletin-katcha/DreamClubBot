from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class StatChannel(SQLModel, table=True):
    """
    Canais de voz que exibem contadores.
    """
    __tablename__ = "stat_channels"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger, index=True))
    channel_id: int = Field(sa_column=Column(BigInteger, unique=True))
    
    # Tipo de contador: 'members', 'online', 'bots', 'date', 'goal'
    stat_type: str = Field(description="Tipo de estatística")
    
    # Formato personalizado (Ex: "👥 Membros: {count}")
    name_format: str = Field(default="{count}", description="Template do nome")