from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.reaction_role import ReactionRole

class ReactionRoleService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_reaction_role(self, guild_id: int, channel_id: int, message_id: int, emoji: str, role_id: int) -> ReactionRole:
        """Cria um novo vínculo de Reação -> Cargo."""
        # Verifica se já existe para evitar duplicados
        stmt = select(ReactionRole).where(
            ReactionRole.message_id == message_id,
            ReactionRole.emoji == emoji
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if existing:
            existing.role_id = role_id # Atualiza o cargo se já existir
            self.session.add(existing)
            await self.session.commit()
            return existing

        rr = ReactionRole(
            guild_id=guild_id,
            channel_id=channel_id,
            message_id=message_id,
            emoji=emoji,
            role_id=role_id
        )
        self.session.add(rr)
        await self.session.commit()
        return rr

    async def get_role_by_reaction(self, message_id: int, emoji: str) -> ReactionRole | None:
        """Busca qual cargo dar baseado na mensagem e emoji clicado."""
        stmt = select(ReactionRole).where(
            ReactionRole.message_id == message_id,
            ReactionRole.emoji == emoji
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_reaction_role(self, message_id: int, emoji: str) -> bool:
        """Remove uma configuração."""
        rr = await self.get_role_by_reaction(message_id, emoji)
        if rr:
            await self.session.delete(rr)
            await self.session.commit()
            return True
        return False