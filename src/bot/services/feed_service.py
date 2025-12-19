from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from bot.models.feed import NewsFeed
from datetime import datetime

class FeedService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_feed(self, guild_id: int, channel_id: int, name: str, url: str, feed_type: str = "rss") -> NewsFeed:
        feed = NewsFeed(
            guild_id=guild_id,
            channel_id=channel_id,
            name=name,
            url=url,
            feed_type=feed_type
        )
        self.session.add(feed)
        await self.session.commit()
        return feed

    async def get_all_feeds(self) -> list[NewsFeed]:
        """Retorna todos os feeds cadastrados para o loop verificar."""
        stmt = select(NewsFeed)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_last_post(self, feed_id: int, post_url: str):
        """Atualiza o registo do último post visto."""
        feed = await self.session.get(NewsFeed, feed_id)
        if feed:
            feed.last_post_url = post_url
            feed.updated_at = datetime.utcnow()
            self.session.add(feed)
            await self.session.commit()

    async def remove_feed(self, feed_id: int):
        feed = await self.session.get(NewsFeed, feed_id)
        if feed:
            await self.session.delete(feed)
            await self.session.commit()