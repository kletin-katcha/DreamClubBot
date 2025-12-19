from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.server_stats import StatChannel

class StatsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_stat_entry(self, guild_id: int, channel_id: int, stat_type: str, name_format: str) -> StatChannel:
        stat = StatChannel(
            guild_id=guild_id,
            channel_id=channel_id,
            stat_type=stat_type,
            name_format=name_format
        )
        self.session.add(stat)
        await self.session.commit()
        return stat

    async def get_guild_stats(self, guild_id: int) -> list[StatChannel]:
        """Retorna todos os contadores de um servidor."""
        stmt = select(StatChannel).where(StatChannel.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def remove_stat(self, channel_id: int):
        stmt = select(StatChannel).where(StatChannel.channel_id == channel_id)
        result = await self.session.execute(stmt)
        stat = result.scalar_one_or_none()
        if stat:
            await self.session.delete(stat)
            await self.session.commit()