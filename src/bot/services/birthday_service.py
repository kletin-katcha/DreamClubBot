from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.birthday import Birthday
from datetime import date

class BirthdayService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def set_birthday(self, user_id: int, day: int, month: int) -> Birthday:
        """Define ou atualiza o aniversário de um membro."""
        # Verifica se já existe
        stmt = select(Birthday).where(Birthday.user_id == user_id)
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.day = day
            existing.month = month
            self.session.add(existing)
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        
        # Cria novo
        bday = Birthday(user_id=user_id, day=day, month=month)
        self.session.add(bday)
        await self.session.commit()
        await self.session.refresh(bday)
        return bday

    async def get_todays_birthdays(self) -> list[Birthday]:
        """Retorna a lista de aniversariantes do dia de hoje."""
        today = date.today()
        stmt = select(Birthday).where(
            Birthday.day == today.day,
            Birthday.month == today.month
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_birthday(self, user_id: int) -> Birthday | None:
        stmt = select(Birthday).where(Birthday.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()