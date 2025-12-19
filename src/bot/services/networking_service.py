from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.networking import UserSkill

class NetworkingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_skill(self, user_id: int, skill: str) -> UserSkill | None:
        """Adiciona uma habilidade ao perfil (se não existir e limite não excedido)."""
        skill_clean = skill.lower().strip()
        
        # 1. Verifica duplicidade
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill == skill_clean
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return None # Já tem essa skill

        # 2. Verifica limite (Máx 10 skills por pessoa)
        count_stmt = select(UserSkill).where(UserSkill.user_id == user_id)
        current_skills = (await self.session.execute(count_stmt)).all()
        if len(current_skills) >= 10:
            return None # Limite atingido

        # 3. Adiciona
        new_skill = UserSkill(user_id=user_id, skill=skill_clean)
        self.session.add(new_skill)
        await self.session.commit()
        return new_skill

    async def remove_skill(self, user_id: int, skill: str) -> bool:
        """Remove uma habilidade."""
        skill_clean = skill.lower().strip()
        stmt = select(UserSkill).where(
            UserSkill.user_id == user_id,
            UserSkill.skill == skill_clean
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if existing:
            await self.session.delete(existing)
            await self.session.commit()
            return True
        return False

    async def get_user_skills(self, user_id: int) -> list[str]:
        """Retorna a lista de skills de um usuário."""
        stmt = select(UserSkill.skill).where(UserSkill.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_users_by_skill(self, skill: str) -> list[int]:
        """Busca IDs de usuários que têm uma skill (busca parcial)."""
        skill_clean = skill.lower().strip()
        # Usa 'contains' para achar "Python" se buscar "py"
        stmt = select(UserSkill.user_id).where(UserSkill.skill.contains(skill_clean))
        result = await self.session.execute(stmt)
        # Retorna lista única de IDs (set)
        return list(set(result.scalars().all()))