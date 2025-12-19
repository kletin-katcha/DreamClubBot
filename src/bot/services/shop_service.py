from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.shop import ShopItem
from bot.models.user import User
import logging

logger = logging.getLogger(__name__)

class ShopService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_item(self, name: str, price: int, role_id: int, description: str = None) -> ShopItem:
        item = ShopItem(name=name, price=price, role_id=role_id, description=description)
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def list_items(self) -> list[ShopItem]:
        result = await self.session.execute(select(ShopItem))
        return result.scalars().all()

    async def buy_item(self, user_id: int, item_id: int) -> tuple[bool, str, ShopItem | None]:
        # 1. Busca o Item
        item = await self.session.get(ShopItem, item_id)
        if not item:
            return False, "Item não encontrado.", None

        # 2. Busca o Usuário
        # Nota: Usamos get_or_create indiretamente via consulta, 
        # mas idealmente o UserService deveria ser injetado ou usado.
        # Aqui fazemos a query direta para simplificar neste contexto de service.
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return False, "Perfil não encontrado. Use o bot primeiro!", None

        # 3. Verifica Saldo (DreamCoins)
        if user.dream_coins < item.price:
            return False, f"Saldo insuficiente. Precisas de DC$ {item.price}, tens DC$ {user.dream_coins}.", item

        # 4. Deduz as Moedas (Transação)
        user.dream_coins -= item.price
        self.session.add(user)
        await self.session.commit()
        
        return True, "Compra realizada com sucesso!", item