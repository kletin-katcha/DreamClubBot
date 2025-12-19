import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.core.database import get_session
from bot.services.notification_service import NotificationService
from bot.utils.embeds import EmbedFactory, DreamColors
import aiohttp
import logging

logger = logging.getLogger(__name__)

class DealsNotifier(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_deals_loop.start()

    def cog_unload(self):
        self.check_deals_loop.cancel()

    @tasks.loop(minutes=30)
    async def check_deals_loop(self):
        await self.bot.wait_until_ready()
        
        # URL simplificada para evitar rejeição
        url = "https://www.gamerpower.com/api/giveaways?type=game&platform=pc.ps4.ps5.xbox-one.xbox-series-xs&sort-by=date"
        
        # Cabeçalhos para fingir ser um navegador real (CRÍTICO)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status != 200:
                        logger.warning(f"GamerPower API status: {resp.status}")
                        return
                    deals = await resp.json()
        except Exception as e:
            logger.error(f"Erro ao buscar deals: {e}")
            return

        if not deals: return

        latest = deals[0]
        game_id = str(latest.get("id"))
        title = latest.get("title")
        description = latest.get("description")
        image = latest.get("image")
        link = latest.get("open_giveaway_url")
        price = latest.get("worth", "N/A")
        platform = latest.get("platforms", "Várias")
        end_date = latest.get("end_date", "Indefinido")

        async with get_session() as session:
            service = NotificationService(session)
            configs = await service.get_all_configs()

            for config in configs:
                if not config.free_games_channel_id or config.last_game_id == game_id:
                    continue

                channel = self.bot.get_channel(config.free_games_channel_id)
                if not channel: continue

                # Uso da Fábrica de Embeds
                embed = EmbedFactory.create(
                    title=f"🎁 Jogo Grátis: {title}",
                    description=f"{description[:200]}...\n\n**[Clique aqui para resgatar!]({link})**",
                    color=discord.Color.from_rgb(114, 137, 218),
                    image=image,
                    footer="Fonte: GamerPower"
                )
                embed.add_field(name="💰 Valor", value=f"~~{price}~~ **GRÁTIS**", inline=True)
                embed.add_field(name="🎮 Plataforma", value=platform, inline=True)
                embed.add_field(name="⏰ Expira", value=end_date, inline=True)

                msg_content = "🚨 **Novo Loot Detectado!**"
                if config.mention_role_id:
                    msg_content += f" <@&{config.mention_role_id}>"

                try:
                    await channel.send(content=msg_content, embed=embed)
                    await service.update_last_game(config.guild_id, game_id)
                except Exception as e:
                    pass

    @app_commands.command(name="config_ofertas", description="[Admin] Define o canal para receber jogos grátis.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_ofertas(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        async with get_session() as session:
            service = NotificationService(session)
            await service.set_channel(interaction.guild.id, "free_games", canal.id)
        
        await interaction.followup.send(embed=EmbedFactory.success(f"Jogos grátis aparecerão em {canal.mention}."))

    @app_commands.command(name="oferta_teste", description="[Admin] Testa o envio de ofertas.")
    @app_commands.checks.has_permissions(administrator=True)
    async def oferta_teste(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.check_deals_loop()
        await interaction.followup.send(embed=EmbedFactory.create(title="Verificação Manual", description="Procurando ofertas...", color=DreamColors.INFO))

async def setup(bot: commands.Bot):
    await bot.add_cog(DealsNotifier(bot))