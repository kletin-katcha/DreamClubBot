from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import BigInteger, Column

class LibraryResource(SQLModel, table=True):
    """
    Representa um recurso de estudo (Livro, Vídeo, etc.) sugerido pelos membros.
    """
    __tablename__ = "library_resources"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Quem sugeriu
    submitter_id: int = Field(sa_column=Column(BigInteger))
    
    title: str = Field(description="Título do material")
    link: str = Field(description="URL para acesso")
    category: str = Field(description="Categoria (Livro, Podcast, Vídeo, Artigo)")
    
    approved: bool = Field(default=False, description="Se foi aprovado pela moderação")
    created_at: datetime = Field(default_factory=datetime.utcnow)