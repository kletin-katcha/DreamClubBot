import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.guild_service import GuildService
from bot.utils.embeds import EmbedFactory, DreamColors
import logging

logger = logging.getLogger(__name__)

class Welcome(commands.Cog):
    """
    Sistema de Onboarding: Recebe novos membros e atribui cargos iniciais.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def format_message(self, text: str, member: discord.Member) -> str:
        return text.format(
            usuario=member.mention,
            nome=member.display_name,
            servidor=member.guild.name,
            contador=member.guild.member_count
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(member.guild.id)

        if not config.module_welcome:
            return

        # 1. AutoRole
        if config.welcome_role_id:
            role = member.guild.get_role(config.welcome_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="AutoRole de Entrada")
                except discord.Forbidden:
                    logger.warning(f"Sem permissão para dar cargo em {member.guild.name}")

        # 2. Mensagem de Boas-Vindas
        if config.welcome_channel_id:
            channel = member.guild.get_channel(config.welcome_channel_id)
            if channel:
                raw_text = config.welcome_message_text or "Bem-vindo {usuario}!"
                try:
                    final_text = self.format_message(raw_text, member)
                except Exception:
                    final_text = f"Bem-vindo {member.mention} ao {member.guild.name}!"

                # USANDO A FÁBRICA AQUI
                embed = EmbedFactory.create(
                    title="👋 Novo Membro!",
                    description=final_text,
                    color=discord.Color.gold(),
                    thumbnail=member.display_avatar.url,
                    footer=f"Membro #{member.guild.member_count} • ID: {member.id}"
                )
                
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    pass

    @app_commands.command(name="config_boasvindas", description="[Admin] Define o canal de entrada.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(interaction.guild.id)
            config.welcome_channel_id = canal.id
            config.module_welcome = True 
            session.add(config)
            await session.commit()
            
        embed = EmbedFactory.success(f"Canal definido para {canal.mention} e módulo ativado.", "Configuração Salva")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="config_mensagem_entrada", description="[Admin] Define a mensagem de texto das boas-vindas.")
    @app_commands.describe(mensagem="Use {usuario}, {servidor}, {contador} como variáveis.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_welcome_msg(self, interaction: discord.Interaction, mensagem: str):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(interaction.guild.id)
            config.welcome_message_text = mensagem
            session.add(config)
            await session.commit()
            
        example = mensagem.replace("{usuario}", interaction.user.mention).replace("{servidor}", interaction.guild.name).replace("{contador}", str(interaction.guild.member_count))
        
        embed = EmbedFactory.create(
            title="Mensagem Atualizada",
            description=f"**Exemplo de visualização:**\n\n{example}",
            color=DreamColors.SUCCESS
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="config_autorole", description="[Admin] Define o cargo que novos membros ganham.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_autorole(self, interaction: discord.Interaction, cargo: discord.Role):
        if cargo >= interaction.guild.me.top_role:
            await interaction.response.send_message(embed=EmbedFactory.error("Esse cargo é superior ao meu."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = GuildService(session)
            await service.set_autorole(interaction.guild.id, cargo.id)
            
        await interaction.followup.send(embed=EmbedFactory.success(f"Cargo automático: **{cargo.name}**"))

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))