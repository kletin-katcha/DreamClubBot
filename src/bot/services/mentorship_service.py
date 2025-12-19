from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from bot.models.mentorship import Mentorship
from bot.models.user import User

class MentorshipService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_mentor(self, apprentice_id: int) -> Mentorship | None:
        """Verifica quem é o mentor deste usuário."""
        stmt = select(Mentorship).where(
            Mentorship.apprentice_id == apprentice_id,
            Mentorship.active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_apprentices_count(self, mentor_id: int) -> int:
        """Conta quantos aprendizes ativos um mentor tem."""
        stmt = select(func.count(Mentorship.id)).where(
            Mentorship.mentor_id == mentor_id,
            Mentorship.active == True
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create_mentorship(self, mentor_id: int, apprentice_id: int) -> tuple[bool, str]:
        """Cria o vínculo."""
        # 1. Verifica requisitos do Mentor (Nível mínimo 5)
        stmt_mentor = select(User).where(User.id == mentor_id)
        mentor = (await self.session.execute(stmt_mentor)).scalar_one_or_none()
        
        if not mentor or mentor.nivel < 5:
            return False, "O Mentor precisa ser pelo menos Nível 5 para ensinar."

        # 2. Verifica se Aprendiz já tem mentor
        if await self.get_mentor(apprentice_id):
            return False, "Este usuário já tem um mentor."
            
        # 3. Verifica limite de aprendizes (Máx 3 por mentor)
        count = await self.get_apprentices_count(mentor_id)
        if count >= 3:
            return False, "O Mentor já atingiu o limite de 3 aprendizes."

        # Cria
        link = Mentorship(mentor_id=mentor_id, apprentice_id=apprentice_id)
        self.session.add(link)
        await self.session.commit()
        return True, "Mentoria iniciada com sucesso!"

    async def end_mentorship(self, apprentice_id: int) -> bool:
        """Encerra o contrato."""
        link = await self.get_mentor(apprentice_id)
        if link:
            link.active = False
            self.session.add(link)
            await self.session.commit()
            return True
        return False