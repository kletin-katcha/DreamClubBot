from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.giveaway import Giveaway
from datetime import datetime

class GiveawayService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_giveaway(self, guild_id: int, channel_id: int, message_id: int, prize: str, end_time: datetime, winners: int) -> Giveaway:
        gw = Giveaway(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            prize=prize,
            end_time=end_time,
            winners_count=winners,
            active=True
        )
        self.session.add(gw)
        await self.session.commit()
        return gw

    async def get_active_giveaways(self) -> list[Giveaway]:
        """Busca todos os sorteios que ainda não terminaram."""
        stmt = select(Giveaway).where(Giveaway.active == True)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def end_giveaway(self, message_id: int):
        """Marca o sorteio como finalizado no banco."""
        stmt = select(Giveaway).where(Giveaway.message_id == message_id)
        result = await self.session.execute(stmt)
        gw = result.scalar_one_or_none()
        
        if gw:
            gw.active = False
            self.session.add(gw)
            await self.session.commit()
        return gw