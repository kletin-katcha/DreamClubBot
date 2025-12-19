from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from bot.models.journal import JournalEntry

class JournalService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_entry(self, user_id: int, content: str) -> JournalEntry:
        """Adiciona uma nova página ao diário."""
        entry = JournalEntry(user_id=user_id, content=content)
        self.session.add(entry)
        await self.session.commit()
        await self.session.refresh(entry)
        return entry

    async def get_user_entries(self, user_id: int, limit: int = 5) -> list[JournalEntry]:
        """
        Recupera as últimas entradas do usuário.
        Ordena da mais recente para a mais antiga.
        """
        statement = select(JournalEntry).where(
            JournalEntry.user_id == user_id
        ).order_by(desc(JournalEntry.created_at)).limit(limit)
        
        result = await self.session.execute(statement)
        return result.scalars().all()