from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from datetime import datetime
from bot.models.goal import Goal
import logging

logger = logging.getLogger(__name__)

class GoalService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_goal(self, user_id: int, description: str) -> Goal:
        """Cria uma nova meta para o usuário."""
        # Limite de segurança: impedir spam de metas (opcional, mas recomendado)
        # Por simplicidade, vamos permitir ilimitado por agora.
        goal = Goal(user_id=user_id, description=description)
        self.session.add(goal)
        await self.session.commit()
        await self.session.refresh(goal)
        return goal

    async def list_pending_goals(self, user_id: int) -> list[Goal]:
        """Lista todas as metas não concluídas do usuário."""
        statement = select(Goal).where(
            Goal.user_id == user_id, 
            Goal.completed == False
        ).order_by(Goal.created_at)
        
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def complete_goal(self, goal_id: int, user_id: int) -> Optional[Goal]:
        """
        Marca uma meta como concluída.
        Verifica se a meta pertence mesmo ao usuário para segurança.
        """
        statement = select(Goal).where(
            Goal.id == goal_id,
            Goal.user_id == user_id
        )
        result = await self.session.execute(statement)
        goal = result.scalar_one_or_none()

        if goal and not goal.completed:
            goal.completed = True
            goal.completed_at = datetime.utcnow()
            self.session.add(goal)
            await self.session.commit()
            await self.session.refresh(goal)
            return goal
        
        return None