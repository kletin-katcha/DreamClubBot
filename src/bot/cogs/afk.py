import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.afk_service import AFKService
from bot.utils.embeds import EmbedFactory, DreamColors
import datetime

class AFK(commands.Cog):
    """
    Sistema de Notificação de Ausência (Away From Keyboard).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="afk", description="Define o seu status como ausente.")
    @app_commands.describe(motivo="Por que você vai sair?")
    async def afk(self, interaction: discord.Interaction, motivo: str = "Ocupado"):
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = AFKService(session)
            await service.set_afk(interaction.user.id, interaction.guild.id, motivo)

        try:
            if interaction.user.display_name.startswith("[AFK] "):
                new_nick = interaction.user.display_name
            else:
                new_nick = f"[AFK] {interaction.user.display_name}"[:32]
            
            await interaction.user.edit(nick=new_nick)
        except discord.Forbidden:
            pass

        embed = EmbedFactory.create(
            title="💤 AFK Ativado",
            description=f"Vou avisar quem te mencionar.\n**Motivo:** {motivo}",
            color=discord.Color.dark_purple()
        )
        await interaction.followup.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        async with get_session() as session:
            service = AFKService(session)

            # 1. Voltou do AFK?
            if not message.content.startswith("/afk"):
                was_afk = await service.remove_afk(message.author.id)
                if was_afk:
                    # Mensagem simples de boas-vindas
                    await message.channel.send(f"👋 Bem-vindo de volta, {message.author.mention}! Removi o teu AFK.", delete_after=5)
                    try:
                        name = message.author.display_name
                        if name.startswith("[AFK] "):
                            await message.author.edit(nick=name.replace("[AFK] ", "", 1))
                    except: pass

            # 2. Mencionou alguém AFK?
            if message.mentions:
                for mentioned in message.mentions:
                    if mentioned.id == message.author.id:
                        continue

                    afk_data = await service.get_afk_status(mentioned.id)
                    if afk_data:
                        start_ts = int(afk_data.start_time.timestamp())
                        
                        embed = EmbedFactory.create(
                            description=f"**Motivo:** {afk_data.reason}\n⏳ **Desde:** <t:{start_ts}:R>",
                            color=DreamColors.WARNING,
                            author=mentioned,
                            footer="Este usuário está ausente."
                        )
                        await message.reply(embed=embed, delete_after=10)

async def setup(bot: commands.Bot):
    await bot.add_cog(AFK(bot))