from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from bot.models.challenge import Challenge, ChallengeCompletion
import logging

logger = logging.getLogger(__name__)

class ChallengeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_challenge(self, title: str, description: str, xp: int) -> Challenge:
        """Cria e ativa um novo desafio global."""
        # Opcional: Desativar desafios anteriores automaticamente
        # statement = select(Challenge).where(Challenge.active == True)
        # ... lógica para desativar ...
        
        challenge = Challenge(title=title, description=description, xp_reward=xp)
        self.session.add(challenge)
        await self.session.commit()
        await self.session.refresh(challenge)
        return challenge

    async def get_active_challenge(self) -> Challenge | None:
        """Busca o desafio ativo mais recente."""
        statement = select(Challenge).where(Challenge.active == True).order_by(desc(Challenge.created_at))
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def complete_challenge(self, user_id: int, challenge_id: int) -> bool:
        """
        Marca o desafio como completo para o utilizador.
        Retorna True se for a primeira vez (sucesso), False se já tinha completado.
        """
        # Verifica se já completou
        statement = select(ChallengeCompletion).where(
            ChallengeCompletion.user_id == user_id,
            ChallengeCompletion.challenge_id == challenge_id
        )
        result = await self.session.execute(statement)
        if result.scalar_one_or_none():
            return False # Já completou antes

        # Marca como completo
        completion = ChallengeCompletion(user_id=user_id, challenge_id=challenge_id)
        self.session.add(completion)
        await self.session.commit()
        return True
    
    async def close_challenge(self, challenge_id: int):
        """Desativa um desafio."""
        challenge = await self.session.get(Challenge, challenge_id)
        if challenge:
            challenge.active = False
            self.session.add(challenge)
            await self.session.commit()