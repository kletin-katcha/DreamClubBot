from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class NewsFeed(SQLModel, table=True):
    """
    Representa uma fonte de notícias (YouTube/RSS) que o bot monitoriza.
    """
    __tablename__ = "news_feeds"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger, index=True))
    channel_id: int = Field(sa_column=Column(BigInteger)) # Canal onde postar
    role_id_to_ping: Optional[int] = Field(default=None, sa_column=Column(BigInteger)) # Cargo para mencionar
    
    name: str = Field(description="Nome do feed (ex: Canal do Dream Club)")
    url: str = Field(description="URL do RSS ou ID do canal YT")
    feed_type: str = Field(default="rss") # rss, youtube
    
    last_post_url: Optional[str] = Field(default=None, description="Link do último post detectado para evitar duplicatas")
    updated_at: datetime = Field(default_factory=datetime.utcnow)