from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.level_reward import LevelReward

class LevelService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_reward(self, guild_id: int, level: int, role_id: int) -> LevelReward:
        """Cria ou atualiza uma recompensa para um nível."""
        # Verifica se já existe recompensa para este nível
        stmt = select(LevelReward).where(
            LevelReward.guild_id == guild_id,
            LevelReward.level_required == level
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing:
            existing.role_id = role_id
            self.session.add(existing)
            await self.session.commit()
            return existing

        reward = LevelReward(guild_id=guild_id, level_required=level, role_id=role_id)
        self.session.add(reward)
        await self.session.commit()
        return reward

    async def get_rewards_for_level(self, guild_id: int, level: int) -> list[LevelReward]:
        """Busca recompensas para o nível atingido."""
        stmt = select(LevelReward).where(
            LevelReward.guild_id == guild_id,
            LevelReward.level_required == level
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_rewards(self, guild_id: int) -> list[LevelReward]:
        """Lista todas as recompensas configuradas no servidor."""
        stmt = select(LevelReward).where(LevelReward.guild_id == guild_id).order_by(LevelReward.level_required)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def remove_reward(self, guild_id: int, level: int) -> bool:
        stmt = select(LevelReward).where(
            LevelReward.guild_id == guild_id,
            LevelReward.level_required == level
        )
        reward = (await self.session.execute(stmt)).scalar_one_or_none()
        if reward:
            await self.session.delete(reward)
            await self.session.commit()
            return True
        return False