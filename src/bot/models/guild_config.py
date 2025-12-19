from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class GuildConfig(SQLModel, table=True):
    """
    Configurações específicas por servidor.
    """
    __tablename__ = "guild_configs"
    # A LINHA MÁGICA ABAIXO CORRIGE O ERRO DA API
    __table_args__ = {'extend_existing': True}

    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    
    # IDs
    welcome_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    welcome_role_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    voice_hub_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    voice_category_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    ticket_category_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    log_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    suggestion_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    report_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    confession_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    free_games_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    tech_news_channel_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    mention_role_id: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    last_game_id: Optional[str] = Field(default=None)

    # Personalização
    welcome_message_text: str = Field(
        default="Olá {usuario}, bem-vindo ao {servidor}!\nVocê é o membro #{contador}.\nDivirta-se!",
        description="Mensagem de texto das boas-vindas"
    )

    # Interruptores
    module_welcome: bool = Field(default=True)
    module_goodbye: bool = Field(default=True)
    module_levels: bool = Field(default=True)
    module_economy: bool = Field(default=True)
    module_music: bool = Field(default=True)
    module_tickets: bool = Field(default=True)
    module_logs: bool = Field(default=True)
    module_fun: bool = Field(default=True)
    module_automod: bool = Field(default=True)
    module_suggestions: bool = Field(default=True)
    module_reports: bool = Field(default=True)
    module_giveaways: bool = Field(default=True)
    module_events: bool = Field(default=True)
    module_networking: bool = Field(default=True)