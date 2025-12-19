from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from bot.models.user import User
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_user(self, user_id: int) -> User:
        statement = select(User).where(User.id == user_id)
        result = await self.session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            user = User(id=user_id)
            self.session.add(user)
            await self.session.flush()
        
        return user

    # --- XP (Maturidade) ---
    async def add_xp(self, user_id: int, amount: int) -> bool:
        """Adiciona XP. Retorna True se subiu de nível."""
        user = await self.get_or_create_user(user_id)
        user.xp_maturidade += amount
        
        leveled_up = False
        xp_needed = user.proximo_nivel_xp

        if user.xp_maturidade >= xp_needed:
            user.xp_maturidade -= xp_needed
            user.nivel += 1
            leveled_up = True
            logger.info(f"Utilizador {user_id} subiu para o nível {user.nivel}")

        await self.session.commit()
        return leveled_up

    # --- DreamCoins ---
    async def add_coins(self, user_id: int, amount: int) -> int:
        user = await self.get_or_create_user(user_id)
        user.dream_coins += amount
        await self.session.commit()
        return user.dream_coins

    async def remove_coins(self, user_id: int, amount: int) -> bool:
        user = await self.get_or_create_user(user_id)
        if user.dream_coins < amount: return False
        user.dream_coins -= amount
        await self.session.commit()
        return True

    async def transfer_coins(self, sender_id: int, receiver_id: int, amount: int) -> bool:
        sender = await self.get_or_create_user(sender_id)
        if sender.dream_coins < amount: return False
        receiver = await self.get_or_create_user(receiver_id)
        sender.dream_coins -= amount
        receiver.dream_coins += amount
        await self.session.commit()
        return True

    # --- Utilitários ---
    async def update_bio(self, user_id: int, new_bio: str) -> User:
        user = await self.get_or_create_user(user_id)
        user.bio_estoica = new_bio
        await self.session.commit()
        return user

    async def get_profile(self, user_id: int) -> User:
        return await self.get_or_create_user(user_id)

    async def get_leaderboard(self, limit: int = 10) -> list[User]:
        statement = select(User).order_by(desc(User.nivel), desc(User.xp_maturidade)).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()
    
    async def get_rich_list(self, limit: int = 10) -> list[User]:
        statement = select(User).order_by(desc(User.dream_coins)).limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()