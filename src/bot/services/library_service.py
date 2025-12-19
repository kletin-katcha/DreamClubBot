from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc
from bot.models.library import LibraryResource
import logging

logger = logging.getLogger(__name__)

class LibraryService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def suggest_resource(self, user_id: int, title: str, link: str, category: str) -> LibraryResource:
        """Adiciona uma sugestão pendente de aprovação."""
        resource = LibraryResource(
            submitter_id=user_id,
            title=title,
            link=link,
            category=category,
            approved=False
        )
        self.session.add(resource)
        await self.session.commit()
        await self.session.refresh(resource)
        return resource

    async def approve_resource(self, resource_id: int) -> LibraryResource | None:
        """Aprova um recurso (Admin)."""
        resource = await self.session.get(LibraryResource, resource_id)
        if resource:
            resource.approved = True
            self.session.add(resource)
            await self.session.commit()
            await self.session.refresh(resource)
            return resource
        return None

    async def delete_resource(self, resource_id: int) -> bool:
        """Remove um recurso (Rejeição ou Limpeza)."""
        resource = await self.session.get(LibraryResource, resource_id)
        if resource:
            await self.session.delete(resource)
            await self.session.commit()
            return True
        return False

    async def list_approved(self, category: str = None) -> list[LibraryResource]:
        """Lista recursos aprovados (opcionalmente filtrados por categoria)."""
        query = select(LibraryResource).where(LibraryResource.approved == True)
        
        if category:
            query = query.where(LibraryResource.category == category)
            
        query = query.order_by(desc(LibraryResource.created_at))
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_pending(self) -> list[LibraryResource]:
        """Lista sugestões aguardando aprovação."""
        query = select(LibraryResource).where(LibraryResource.approved == False).order_by(LibraryResource.created_at)
        result = await self.session.execute(query)
        return result.scalars().all()