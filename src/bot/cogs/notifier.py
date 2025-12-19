import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.core.database import get_session
from bot.services.feed_service import FeedService
import feedparser # Biblioteca necessária: pip install feedparser
import asyncio

class Notifier(commands.Cog):
    """
    Sistema de Notificação de Notícias e Vídeos.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_feeds_loop.start()

    def cog_unload(self):
        self.check_feeds_loop.cancel()

    @tasks.loop(minutes=15)
    async def check_feeds_loop(self):
        """Verifica novidades em todos os feeds registados."""
        await self.bot.wait_until_ready()

        async with get_session() as session:
            service = FeedService(session)
            feeds = await service.get_all_feeds()

            for feed in feeds:
                try:
                    # Executa o parser num executor para não bloquear o bot (I/O)
                    # feedparser é síncrono, então precisamos disto
                    data = await self.bot.loop.run_in_executor(None, feedparser.parse, feed.url)
                    
                    if not data.entries:
                        continue

                    # Pega o post mais recente (primeiro da lista)
                    latest_entry = data.entries[0]
                    link = latest_entry.link
                    title = latest_entry.title

                    # Verifica se é novo
                    if feed.last_post_url != link:
                        # É NOVO! Vamos anunciar.
                        channel = self.bot.get_channel(feed.channel_id)
                        if channel:
                            msg_content = f"📢 **Nova atualização de {feed.name}!**"
                            if feed.role_id_to_ping:
                                msg_content += f" <@&{feed.role_id_to_ping}>"
                            
                            msg_content += f"\n\n**{title}**\n{link}"
                            
                            await channel.send(msg_content)
                            
                            # Atualiza o banco
                            await service.update_last_post(feed.id, link)
                        else:
                            # Se o canal não existe mais, talvez deletar o feed?
                            pass

                except Exception as e:
                    print(f"Erro ao verificar feed {feed.name}: {e}")

    @app_commands.command(name="feed_adicionar", description="[Admin] Adiciona um feed RSS ou Canal do YouTube.")
    @app_commands.choices(tipo=[
        app_commands.Choice(name="YouTube", value="youtube"),
        app_commands.Choice(name="RSS Site/Blog", value="rss")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def feed_add(self, interaction: discord.Interaction, nome: str, url: str, canal_discord: discord.TextChannel, tipo: app_commands.Choice[str]):
        # Se for YouTube, precisamos converter a URL do canal para o feed RSS do YouTube
        # Aceita formatos: youtube.com/channel/ID
        final_url = url
        if tipo.value == "youtube":
            if "channel/" in url:
                channel_id = url.split("channel/")[-1].split("/")[0] # Tenta extrair o ID
                final_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            elif "feeds/videos.xml" not in url:
                await interaction.response.send_message("❌ Para YouTube, por favor use o link completo com ID do canal (ex: youtube.com/channel/UC...).\nLinks personalizados (@nome) não funcionam diretamente no RSS.", ephemeral=True)
                return

        await interaction.response.defer()

        async with get_session() as session:
            service = FeedService(session)
            await service.add_feed(interaction.guild.id, canal_discord.id, nome, final_url, tipo.value)

        await interaction.followup.send(f"✅ Feed **{nome}** configurado em {canal_discord.mention}!")

    @app_commands.command(name="feeds_lista", description="[Admin] Vê os feeds ativos.")
    @app_commands.checks.has_permissions(administrator=True)
    async def feed_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = FeedService(session)
            feeds = await service.get_all_feeds()
            
        if not feeds:
            await interaction.followup.send("📭 Nenhum feed configurado.")
            return

        embed = discord.Embed(title="📡 Feeds de Notícias", color=discord.Color.blue())
        for f in feeds:
            embed.add_field(
                name=f"#{f.id} - {f.name} ({f.feed_type.upper()})",
                value=f"Canal: <#{f.channel_id}>\nÚltimo: {f.last_post_url or 'Nenhum'}",
                inline=False
            )
            
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="feed_remover", description="[Admin] Remove um feed.")
    @app_commands.checks.has_permissions(administrator=True)
    async def feed_remove(self, interaction: discord.Interaction, id_feed: int):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = FeedService(session)
            await service.remove_feed(id_feed)
            
        await interaction.followup.send(f"🗑️ Feed #{id_feed} removido.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Notifier(bot))