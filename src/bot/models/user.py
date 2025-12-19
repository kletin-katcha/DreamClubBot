from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class User(SQLModel, table=True):
    """
    Representa um usuário no sistema de Maturidade e Economia.
    """
    __tablename__ = "users"

    id: int = Field(default=None, sa_column=Column(BigInteger, primary_key=True))
    
    # Nível (Maturidade)
    xp_maturidade: int = Field(default=0, description="XP acumulado de maturidade")
    nivel: int = Field(default=1, description="Nível atual de evolução")
    
    # Economia (DreamCoins)
    dream_coins: int = Field(default=0, description="Saldo em DreamCoins (DC$)")
    
    # Controle de Daily
    last_daily: Optional[datetime] = Field(default=None, description="Data do último daily resgatado")
    
    bio_estoica: Optional[str] = Field(default=None, max_length=200, description="Frase pessoal do usuário")

    @property
    def proximo_nivel_xp(self) -> int:
        return self.nivel * 100