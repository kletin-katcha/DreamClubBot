from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.confession import Confession

class ConfessionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_confession(self, guild_id: int, author_id: int, message_id: int, content: str) -> Confession:
        confession = Confession(
            guild_id=guild_id,
            author_id=author_id,
            message_id=message_id,
            content=content
        )
        self.session.add(confession)
        await self.session.commit()
        await self.session.refresh(confession)
        return confession

    async def get_confession(self, id: int) -> Confession | None:
        return await self.session.get(Confession, id)