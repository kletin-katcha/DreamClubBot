from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.starboard import StarboardConfig, StarboardEntry

class StarboardService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self, guild_id: int) -> StarboardConfig | None:
        stmt = select(StarboardConfig).where(StarboardConfig.guild_id == guild_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def set_config(self, guild_id: int, channel_id: int, threshold: int):
        config = await self.get_config(guild_id)
        if not config:
            config = StarboardConfig(guild_id=guild_id, channel_id=channel_id, threshold=threshold)
        else:
            config.channel_id = channel_id
            config.threshold = threshold
        
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def get_entry(self, original_message_id: int) -> StarboardEntry | None:
        stmt = select(StarboardEntry).where(StarboardEntry.original_message_id == original_message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_entry(self, original_id: int, starboard_id: int, channel_id: int, stars: int):
        entry = StarboardEntry(
            original_message_id=original_id,
            starboard_message_id=starboard_id,
            channel_id=channel_id,
            stars=stars
        )
        self.session.add(entry)
        await self.session.commit()

    async def update_stars(self, entry: StarboardEntry, stars: int):
        entry.stars = stars
        self.session.add(entry)
        await self.session.commit()