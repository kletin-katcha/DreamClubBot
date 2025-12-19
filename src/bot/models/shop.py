from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class ShopItem(SQLModel, table=True):
    """
    Representa um item (cargo) à venda na loja.
    """
    __tablename__ = "shop_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # ID do Cargo no Discord que será entregue
    role_id: int = Field(sa_column=Column(BigInteger, unique=True))
    
    name: str = Field(description="Nome do item/cargo")
    price: int = Field(description="Custo em XP")
    description: Optional[str] = Field(default=None, description="Descrição do benefício")