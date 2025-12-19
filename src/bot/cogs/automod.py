import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.guild_service import GuildService
from bot.utils.embeds import EmbedFactory, DreamColors
import re
import datetime

class AutoMod(commands.Cog):
    """
    Sistema automático de proteção.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.invite_regex = re.compile(r'(https?://)?(www\.)?(discord\.(gg|io|me|li)|discordapp\.com/invite)/.+[a-z]')
        self.bad_words = ["palavrao1", "palavrao2", "scam", "casino"]

    async def log_action(self, message: discord.Message, reason: str):
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(message.guild.id)
            
            if config.log_channel_id:
                channel = message.guild.get_channel(config.log_channel_id)
                if channel:
                    # Embed de Log Profissional
                    embed = EmbedFactory.create(
                        title="🛡️ AutoMod Action",
                        description=f"**Infrator:** {message.author.mention} (`{message.author.id}`)\n"
                                    f"**Motivo:** {reason}\n"
                                    f"**Canal:** {message.channel.mention}",
                        color=DreamColors.ERROR
                    )
                    embed.add_field(name="Conteúdo Apagado", value=message.content[:1024] or "*Conteúdo multimédia*", inline=False)
                    await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if message.author.guild_permissions.administrator:
            return

        content_lower = message.content.lower()

        # Anti-Invite
        if self.invite_regex.search(content_lower):
            await message.delete()
            # Aviso efêmero ou temporário
            embed = EmbedFactory.warning(f"{message.author.mention} **Divulgação não é permitida aqui!**")
            await message.channel.send(embed=embed, delete_after=5)
            await self.log_action(message, "Link de Convite (Anti-Invite)")
            return

        # Filtro de Palavras
        for word in self.bad_words:
            if word in content_lower:
                try:
                    await message.delete()
                    embed = EmbedFactory.warning(f"{message.author.mention} ⚠️ Mantenha o nível da conversa.")
                    await message.channel.send(embed=embed, delete_after=5)
                    await self.log_action(message, f"Palavra Bloqueada: {word}")
                    return
                except discord.NotFound:
                    pass

    @app_commands.command(name="config_logs", description="[Admin] Define o canal para logs de moderação.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_logs(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = GuildService(session)
            await service.set_log_channel(interaction.guild.id, canal.id)
            
        await interaction.followup.send(embed=EmbedFactory.success(f"Canal de logs definido para: {canal.mention}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoMod(bot))