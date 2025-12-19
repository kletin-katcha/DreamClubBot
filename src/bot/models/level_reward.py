from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class LevelReward(SQLModel, table=True):
    """
    Define um cargo a ser entregue quando o usuário atinge certo nível.
    """
    __tablename__ = "level_rewards"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    guild_id: int = Field(sa_column=Column(BigInteger, index=True))
    level_required: int = Field(description="Nível necessário para ganhar o cargo")
    role_id: int = Field(sa_column=Column(BigInteger))