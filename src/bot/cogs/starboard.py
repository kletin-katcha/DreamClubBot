import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.starboard_service import StarboardService
import logging

logger = logging.getLogger(__name__)

class Starboard(commands.Cog):
    """
    Sistema de destaque de mensagens (Quadro de Honra).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_star_emoji(self, count: int) -> str:
        if count < 5: return "⭐"
        if count < 10: return "🌟"
        if count < 20: return "✨"
        return "💫"

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        async with get_session() as session:
            service = StarboardService(session)
            config = await service.get_config(payload.guild_id)
            
            # Se não estiver configurado, ignora
            if not config:
                return

            # Busca a mensagem original
            channel = self.bot.get_channel(payload.channel_id)
            try:
                message = await channel.fetch_message(payload.message_id)
            except:
                return

            # Conta as estrelas
            reaction = discord.utils.get(message.reactions, emoji="⭐")
            if not reaction: return
            count = reaction.count

            # Verifica se atingiu o mínimo
            if count < config.threshold:
                return

            # Verifica se já está no starboard
            entry = await service.get_entry(message.id)
            star_channel = self.bot.get_channel(config.channel_id)
            
            if not star_channel:
                return

            # Conteúdo do Embed
            embed = discord.Embed(description=message.content, color=discord.Color.gold())
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Origem", value=f"[Ir para mensagem]({message.jump_url}) em {channel.mention}")
            
            if message.attachments:
                embed.set_image(url=message.attachments[0].url)
            
            embed.timestamp = message.created_at
            
            content = f"{self.get_star_emoji(count)} **{count}** | {channel.mention}"

            if entry:
                # Atualiza mensagem existente
                try:
                    star_msg = await star_channel.fetch_message(entry.starboard_message_id)
                    await star_msg.edit(content=content, embed=embed)
                    await service.update_stars(entry, count)
                except:
                    # Se a mensagem do starboard foi apagada, cria nova? (Opcional)
                    pass
            else:
                # Cria nova mensagem no starboard
                star_msg = await star_channel.send(content=content, embed=embed)
                await service.add_entry(message.id, star_msg.id, channel.id, count)

    @app_commands.command(name="config_starboard", description="[Admin] Configura o canal de destaques.")
    @app_commands.describe(canal="Onde as mensagens vão aparecer", minimo="Mínimo de estrelas (Padrão: 3)")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_starboard(self, interaction: discord.Interaction, canal: discord.TextChannel, minimo: int = 3):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = StarboardService(session)
            await service.set_config(interaction.guild.id, canal.id, minimo)
            
        await interaction.followup.send(f"✅ **Starboard Configurado!**\nCanal: {canal.mention}\nMínimo: {minimo} ⭐")

async def setup(bot: commands.Bot):
    await bot.add_cog(Starboard(bot))