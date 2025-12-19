from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from datetime import datetime, timedelta
from bot.models.habit import Habit
import logging

logger = logging.getLogger(__name__)

class HabitService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_habit(self, user_id: int, name: str) -> Habit:
        """Cria um novo rastreador de hábito."""
        habit = Habit(user_id=user_id, name=name)
        self.session.add(habit)
        await self.session.commit()
        await self.session.refresh(habit)
        return habit

    async def list_user_habits(self, user_id: int) -> list[Habit]:
        """Lista todos os hábitos do utilizador."""
        statement = select(Habit).where(Habit.user_id == user_id)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def check_in(self, habit_id: int, user_id: int) -> tuple[bool, str, Habit | None]:
        """
        Realiza o check-in diário.
        Lógica de Streak:
        - Mesmo dia: Erro (Já fez).
        - Dia seguinte (Ontem -> Hoje): Streak +1.
        - Mais de 1 dia (Antes de ontem -> Hoje): Reset para 1.
        """
        statement = select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
        result = await self.session.execute(statement)
        habit = result.scalar_one_or_none()

        if not habit:
            return False, "Hábito não encontrado.", None

        now = datetime.utcnow()
        
        if habit.last_checkin:
            # Calcula a diferença de dias (ignorando horas/minutos para simplificar)
            last_date = habit.last_checkin.date()
            today_date = now.date()
            diff = (today_date - last_date).days

            if diff == 0:
                return False, "Já fizeste o check-in hoje! Volta amanhã.", habit
            elif diff == 1:
                # Sequência mantida
                habit.current_streak += 1
                msg = f"🔥 Sequência mantida! **{habit.current_streak} dias**."
            else:
                # Perdeu a sequência
                msg = f"⚠️ Sequência perdida (era {habit.current_streak} dias). Começando de novo!"
                habit.current_streak = 1
        else:
            # Primeiro check-in de sempre
            habit.current_streak = 1
            msg = "🚀 Começaste a tua sequência! 1 dia."

        # Atualiza o recorde pessoal
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak

        habit.last_checkin = now
        self.session.add(habit)
        await self.session.commit()
        await self.session.refresh(habit)
        
        return True, msg, habit