from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.afk import AFKStatus

class AFKService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_afk(self, user_id: int, guild_id: int, reason: str) -> AFKStatus:
        """Define o usuário como AFK (atualiza se já existir)."""
        stmt = select(AFKStatus).where(AFKStatus.user_id == user_id)
        result = await self.session.execute(stmt)
        afk = result.scalar_one_or_none()

        if afk:
            afk.reason = reason
            # Não atualizamos o start_time para manter a originalidade se ele reusar o comando
        else:
            afk = AFKStatus(user_id=user_id, guild_id=guild_id, reason=reason)
            self.session.add(afk)
        
        await self.session.commit()
        await self.session.refresh(afk)
        return afk

    async def remove_afk(self, user_id: int) -> bool:
        """Remove o status AFK se existir. Retorna True se removeu."""
        stmt = select(AFKStatus).where(AFKStatus.user_id == user_id)
        result = await self.session.execute(stmt)
        afk = result.scalar_one_or_none()

        if afk:
            await self.session.delete(afk)
            await self.session.commit()
            return True
        return False

    async def get_afk_status(self, user_id: int) -> AFKStatus | None:
        """Verifica se o usuário está AFK."""
        stmt = select(AFKStatus).where(AFKStatus.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()