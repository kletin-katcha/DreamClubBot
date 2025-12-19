from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.suggestion import Suggestion

class SuggestionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_suggestion(self, guild_id: int, author_id: int, message_id: int, content: str) -> Suggestion:
        sug = Suggestion(
            guild_id=guild_id,
            author_id=author_id,
            message_id=message_id,
            content=content,
            status="pending"
        )
        self.session.add(sug)
        await self.session.commit()
        return sug

    async def get_suggestion(self, id: int) -> Suggestion | None:
        return await self.session.get(Suggestion, id)

    async def update_status(self, id: int, status: str) -> Suggestion | None:
        sug = await self.session.get(Suggestion, id)
        if sug:
            sug.status = status
            self.session.add(sug)
            await self.session.commit()
            await self.session.refresh(sug)
        return sug