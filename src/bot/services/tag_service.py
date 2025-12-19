from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from bot.models.tag import Tag

class TagService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_tag(self, guild_id: int, author_id: int, name: str, content: str) -> tuple[Tag | None, str]:
        """Cria uma nova tag."""
        name_clean = name.lower().strip().replace(" ", "_")
        
        # Verifica se já existe neste servidor
        stmt = select(Tag).where(Tag.guild_id == guild_id, Tag.name == name_clean)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if existing:
            return None, "Já existe uma tag com esse nome."

        tag = Tag(guild_id=guild_id, author_id=author_id, name=name_clean, content=content)
        self.session.add(tag)
        await self.session.commit()
        await self.session.refresh(tag)
        return tag, "Tag criada com sucesso."

    async def get_tag(self, guild_id: int, name: str) -> Tag | None:
        """Busca uma tag e incrementa o contador de uso."""
        name_clean = name.lower().strip().replace(" ", "_")
        stmt = select(Tag).where(Tag.guild_id == guild_id, Tag.name == name_clean)
        tag = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if tag:
            tag.uses += 1
            self.session.add(tag)
            await self.session.commit()
            
        return tag

    async def delete_tag(self, guild_id: int, name: str) -> bool:
        """Remove uma tag."""
        name_clean = name.lower().strip()
        stmt = select(Tag).where(Tag.guild_id == guild_id, Tag.name == name_clean)
        tag = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if tag:
            await self.session.delete(tag)
            await self.session.commit()
            return True
        return False

    async def list_tags(self, guild_id: int) -> list[Tag]:
        """Lista todas as tags do servidor."""
        stmt = select(Tag).where(Tag.guild_id == guild_id).order_by(Tag.name)
        result = await self.session.execute(stmt)
        return result.scalars().all()