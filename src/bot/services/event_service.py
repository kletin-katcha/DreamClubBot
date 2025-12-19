from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from bot.models.event import Event, EventParticipant
from datetime import datetime

class EventService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_event(self, guild_id: int, channel_id: int, message_id: int, organizer_id: int, title: str, description: str, start_time: datetime) -> Event:
        event = Event(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            organizer_id=organizer_id,
            title=title,
            description=description,
            start_time=start_time
        )
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def get_event_by_message(self, message_id: int) -> Event | None:
        stmt = select(Event).where(Event.message_id == message_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_participant(self, event_id: int, user_id: int, status: str) -> bool:
        """Adiciona ou atualiza a presença."""
        # Verifica se já existe
        stmt = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        if existing:
            if existing.status == status:
                return False # Nada mudou
            existing.status = status
            self.session.add(existing)
        else:
            participant = EventParticipant(event_id=event_id, user_id=user_id, status=status)
            self.session.add(participant)
        
        await self.session.commit()
        return True

    async def remove_participant(self, event_id: int, user_id: int):
        """Remove a presença."""
        stmt = delete(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_participants(self, event_id: int, status: str) -> list[int]:
        """Retorna lista de user_ids para um status."""
        stmt = select(EventParticipant.user_id).where(
            EventParticipant.event_id == event_id,
            EventParticipant.status == status
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()