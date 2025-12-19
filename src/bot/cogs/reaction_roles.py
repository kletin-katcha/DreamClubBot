import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.reaction_role_service import ReactionRoleService
import logging

logger = logging.getLogger(__name__)

class ReactionRoles(commands.Cog):
    """
    Gerencia a entrega automática de cargos via reações.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Disparado quando alguém reage."""
        if payload.member.bot:
            return

        # Busca no banco se essa reação vale alguma coisa
        async with get_session() as session:
            service = ReactionRoleService(session)
            # O emoji pode ser string (Unicode) ou custom (<:name:id>)
            emoji_str = str(payload.emoji)
            rr = await service.get_role_by_reaction(payload.message_id, emoji_str)

            if rr:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(rr.role_id)
                if role:
                    try:
                        await payload.member.add_roles(role, reason="Reaction Role")
                    except discord.Forbidden:
                        logger.warning(f"Sem permissão para dar cargo {role.name} em {guild.name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Disparado quando alguém remove a reação (tira o cargo)."""
        async with get_session() as session:
            service = ReactionRoleService(session)
            emoji_str = str(payload.emoji)
            rr = await service.get_role_by_reaction(payload.message_id, emoji_str)

            if rr:
                guild = self.bot.get_guild(payload.guild_id)
                role = guild.get_role(rr.role_id)
                member = guild.get_member(payload.user_id)
                
                if role and member:
                    try:
                        await member.remove_roles(role, reason="Reaction Role Removed")
                    except discord.Forbidden:
                        pass

    @app_commands.command(name="rr_add", description="[Admin] Adiciona um cargo por reação a uma mensagem.")
    @app_commands.describe(id_mensagem="ID da mensagem já enviada", emoji="O emoji para reagir", cargo="O cargo a ganhar")
    @app_commands.checks.has_permissions(administrator=True)
    async def rr_add(self, interaction: discord.Interaction, id_mensagem: str, emoji: str, cargo: discord.Role):
        try:
            msg_id = int(id_mensagem)
            message = await interaction.channel.fetch_message(msg_id)
        except:
            await interaction.response.send_message("❌ Mensagem não encontrada neste canal ou ID inválido.", ephemeral=True)
            return

        # Verifica hierarquia
        if cargo >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ O cargo selecionado é superior ao meu.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Adiciona a reação na mensagem para facilitar
        try:
            await message.add_reaction(emoji)
        except Exception as e:
            await interaction.followup.send(f"❌ Não consegui reagir com '{emoji}'. Verifique se é um emoji válido ou se tenho acesso.")
            return

        # Salva no banco
        async with get_session() as session:
            service = ReactionRoleService(session)
            await service.add_reaction_role(
                interaction.guild.id,
                interaction.channel.id,
                msg_id,
                emoji,
                cargo.id
            )

        await interaction.followup.send(f"✅ Configurado! Reagir com {emoji} na mensagem dará o cargo **{cargo.name}**.")

    @app_commands.command(name="rr_remove", description="[Admin] Remove uma configuração de reaction role.")
    @app_commands.checks.has_permissions(administrator=True)
    async def rr_remove(self, interaction: discord.Interaction, id_mensagem: str, emoji: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            msg_id = int(id_mensagem)
        except:
            await interaction.followup.send("❌ ID inválido.")
            return

        async with get_session() as session:
            service = ReactionRoleService(session)
            success = await service.remove_reaction_role(msg_id, emoji)

        if success:
            await interaction.followup.send(f"🗑️ Configuração removida para {emoji}.")
            # Tenta remover a reação do bot da mensagem
            try:
                msg = await interaction.channel.fetch_message(msg_id)
                await msg.remove_reaction(emoji, interaction.guild.me)
            except:
                pass
        else:
            await interaction.followup.send("❌ Configuração não encontrada.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRoles(bot))