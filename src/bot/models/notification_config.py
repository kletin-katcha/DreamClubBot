from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class NotificationConfig(SQLModel, table=True):
    """
    Configurações de feeds automáticos de promoções e jogos.
    """
    __tablename__ = "notification_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    
    # Canais para cada tipo de conteúdo
    free_games_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    tech_news_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    
    # Cargo para mencionar (opcional)
    mention_role_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    
    # Último ID processado para evitar duplicatas
    last_game_id: Optional[str] = Field(default=None)