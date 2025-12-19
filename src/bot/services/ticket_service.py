from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.ticket import Ticket

class TicketService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_ticket(self, guild_id: int, channel_id: int, user_id: int) -> Ticket:
        """Regista um novo ticket."""
        ticket = Ticket(guild_id=guild_id, channel_id=channel_id, user_id=user_id)
        self.session.add(ticket)
        await self.session.commit()
        return ticket

    async def get_ticket_by_channel(self, channel_id: int) -> Ticket | None:
        """Busca um ticket pelo ID do canal."""
        stmt = select(Ticket).where(Ticket.channel_id == channel_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def close_ticket(self, channel_id: int):
        """Marca como fechado."""
        ticket = await self.get_ticket_by_channel(channel_id)
        if ticket:
            ticket.status = "closed"
            self.session.add(ticket)
            await self.session.commit()