from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.reminder import Reminder
from datetime import datetime

class ReminderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_reminder(self, user_id: int, channel_id: int, message: str, due_at: datetime) -> Reminder:
        """Agenda um novo lembrete."""
        reminder = Reminder(
            user_id=user_id,
            channel_id=channel_id,
            message=message,
            due_at=due_at,
            active=True
        )
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def get_due_reminders(self) -> list[Reminder]:
        """Busca lembretes ativos cuja hora já chegou."""
        now = datetime.utcnow()
        stmt = select(Reminder).where(
            Reminder.active == True,
            Reminder.due_at <= now
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def complete_reminder(self, reminder_id: int):
        """Marca como entregue (inativo)."""
        reminder = await self.session.get(Reminder, reminder_id)
        if reminder:
            reminder.active = False
            self.session.add(reminder)
            await self.session.commit()