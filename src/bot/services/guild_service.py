from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.guild_config import GuildConfig

class GuildService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_config(self, guild_id: int) -> GuildConfig:
        stmt = select(GuildConfig).where(GuildConfig.guild_id == guild_id)
        result = await self.session.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            config = GuildConfig(guild_id=guild_id)
            self.session.add(config)
            await self.session.commit()
            await self.session.refresh(config)
        
        return config

    async def set_welcome_channel(self, guild_id: int, channel_id: int) -> GuildConfig:
        config = await self.get_config(guild_id)
        config.welcome_channel_id = channel_id
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def set_autorole(self, guild_id: int, role_id: int) -> GuildConfig:
        config = await self.get_config(guild_id)
        config.welcome_role_id = role_id
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def set_voice_hub(self, guild_id: int, channel_id: int, category_id: int) -> GuildConfig:
        config = await self.get_config(guild_id)
        config.voice_hub_id = channel_id
        config.voice_category_id = category_id
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def set_ticket_category(self, guild_id: int, category_id: int) -> GuildConfig:
        config = await self.get_config(guild_id)
        config.ticket_category_id = category_id
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def set_log_channel(self, guild_id: int, channel_id: int) -> GuildConfig:
        """[NOVO] Define o canal de logs de moderação."""
        config = await self.get_config(guild_id)
        config.log_channel_id = channel_id
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config