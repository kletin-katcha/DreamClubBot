from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.poll import Poll

class PollService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_poll(self, guild_id: int, channel_id: int, message_id: int, author_id: int, question: str, options: str) -> Poll:
        poll = Poll(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            author_id=author_id,
            question=question,
            options=options,
            active=True
        )
        self.session.add(poll)
        await self.session.commit()
        return poll

    async def get_active_poll(self, message_id: int) -> Poll | None:
        stmt = select(Poll).where(Poll.message_id == message_id, Poll.active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def close_poll(self, message_id: int) -> Poll | None:
        poll = await self.get_active_poll(message_id)
        if poll:
            poll.active = False
            self.session.add(poll)
            await self.session.commit()
        return poll