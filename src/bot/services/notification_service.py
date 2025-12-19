from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.notification_config import NotificationConfig

class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self, guild_id: int) -> NotificationConfig:
        stmt = select(NotificationConfig).where(NotificationConfig.guild_id == guild_id)
        result = await self.session.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            config = NotificationConfig(guild_id=guild_id)
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
            
        return config

    async def set_channel(self, guild_id: int, channel_type: str, channel_id: int):
        config = await self.get_config(guild_id)
        if channel_type == "free_games":
            config.free_games_channel_id = channel_id
        elif channel_type == "tech_news":
            config.tech_news_channel_id = channel_id
            
        self.session.add(config)
        await self.session.commit()

    async def update_last_game(self, guild_id: int, game_id: str):
        config = await self.get_config(guild_id)
        config.last_game_id = game_id
        self.session.add(config)
        await self.session.commit()
    
    async def get_all_configs(self) -> list[NotificationConfig]:
        stmt = select(NotificationConfig)
        result = await self.session.execute(stmt)
        return result.scalars().all()