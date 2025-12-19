from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from bot.models.tribe import Tribe, TribeMember
from bot.models.user import User
import logging

logger = logging.getLogger(__name__)

class TribeService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_tribe(self, user_id: int) -> tuple[Tribe | None, TribeMember | None]:
        """Verifica se o utilizador já tem uma tribo. Retorna (Tribo, Membro)."""
        # Busca o registo de membro
        stmt_member = select(TribeMember).where(TribeMember.user_id == user_id)
        result = await self.session.execute(stmt_member)
        member = result.scalar_one_or_none()

        if member:
            # Se é membro, busca os dados da tribo
            tribe = await self.session.get(Tribe, member.tribe_id)
            return tribe, member
        return None, None

    async def create_tribe(self, user_id: int, name: str, description: str) -> tuple[bool, str, Tribe | None]:
        """
        Cria uma tribo.
        Requisitos:
        1. Utilizador não pode estar em outra tribo.
        2. Custo de criação: 1000 XP (deduzido do líder).
        """
        # 1. Verifica se já tem tribo
        tribe, _ = await self.get_user_tribe(user_id)
        if tribe:
            return False, "Já pertences a uma tribo! Sai primeiro.", None

        # 2. Verifica nome duplicado
        stmt_name = select(Tribe).where(Tribe.name == name)
        if (await self.session.execute(stmt_name)).first():
            return False, "Já existe uma tribo com esse nome.", None

        # 3. Verifica XP do Líder (Custo: 1000 XP)
        COST = 1000
        stmt_user = select(User).where(User.id == user_id)
        user = (await self.session.execute(stmt_user)).scalar_one_or_none()
        
        if not user or user.xp_maturidade < COST:
            return False, f"XP Insuficiente. Precisas de {COST} XP para fundar uma tribo.", None

        # 4. Processa Criação
        try:
            # Deduz XP
            user.xp_maturidade -= COST
            self.session.add(user)

            # Cria Tribo
            new_tribe = Tribe(name=name, description=description, leader_id=user_id)
            self.session.add(new_tribe)
            await self.session.flush() # Para gerar o ID da tribo

            # Adiciona Líder como Membro
            member = TribeMember(tribe_id=new_tribe.id, user_id=user_id)
            self.session.add(member)

            await self.session.commit()
            return True, "Tribo fundada com sucesso!", new_tribe
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Erro ao criar tribo: {e}")
            return False, "Erro interno ao criar tribo.", None

    async def add_member(self, tribe_id: int, user_id: int) -> bool:
        """Adiciona um membro à tribo."""
        # Verifica se já tem tribo
        if (await self.get_user_tribe(user_id))[0]:
            return False
            
        member = TribeMember(tribe_id=tribe_id, user_id=user_id)
        self.session.add(member)
        await self.session.commit()
        return True

    async def remove_member(self, user_id: int):
        """Remove um membro da tribo."""
        stmt = select(TribeMember).where(TribeMember.user_id == user_id)
        member = (await self.session.execute(stmt)).scalar_one_or_none()
        if member:
            await self.session.delete(member)
            await self.session.commit()

    async def get_members_count(self, tribe_id: int) -> int:
        """Conta quantos membros a tribo tem."""
        stmt = select(func.count(TribeMember.id)).where(TribeMember.tribe_id == tribe_id)
        return (await self.session.execute(stmt)).scalar_one()