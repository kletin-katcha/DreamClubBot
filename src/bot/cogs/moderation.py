import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """
    Cog responsável pela moderação temática: Choques de Realidade e Controle de Ego.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ego_check", description="Aplica um 'timeout' para reflexão. (Requer permissão de Moderar Membros)")
    @app_commands.describe(membro="O usuário que precisa baixar a bola", motivo="A razão pedagógica para o timeout")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def ego_check(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Comportamento imaturo"):
        """
        Aplica um Timeout de 10 minutos.
        Envia DM educativa e mensagem no chat.
        """
        # Verificações de segurança
        if membro.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode aplicar um ego check em si mesmo.", ephemeral=True)
            return
            
        if membro.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Não consigo punir este usuário pois o cargo dele é superior ou igual ao meu.", ephemeral=True)
            return

        await interaction.response.defer()

        # Define a duração do castigo (10 minutos)
        duracao = timedelta(minutes=10)
        
        try:
            # Aplica o Timeout no Discord
            await membro.timeout(duracao, reason=f"Ego Check: {motivo}")

            # Tenta enviar a DM educativa
            dm_sent = False
            try:
                await membro.send(
                    f"🧘 **Ego Check**\n\n"
                    f"Você deixou seu ego dominar. Tire 10 minutos para refletir sobre humildade e racionalidade.\n"
                    f"**Motivo:** {motivo}"
                )
                dm_sent = True
            except discord.Forbidden:
                logger.warning(f"Não foi possível enviar DM para {membro} (Ego Check).")

            # Feedback público
            msg_publica = f"🛑 **Ego Check Aplicado!**\n{membro.mention} precisou de um tempo para esfriar a cabeça.\n**Motivo:** {motivo}"
            if not dm_sent:
                msg_publica += "\n*(A DM de reflexão não pôde ser entregue, verifique suas privacidades)*"
            
            await interaction.followup.send(msg_publica)
            logger.info(f"{interaction.user} aplicou ego_check em {membro} por: {motivo}")

        except Exception as e:
            await interaction.followup.send(f"❌ Ocorreu um erro ao tentar aplicar o timeout: {str(e)}")
            logger.error(f"Erro no comando ego_check: {e}")

    @app_commands.command(name="realidade", description="Expulsa um usuário que não está pronto. (Requer permissão de Expulsar)")
    @app_commands.describe(membro="O usuário a ser removido", motivo="Motivo da expulsão")
    @app_commands.checks.has_permissions(kick_members=True)
    async def realidade(self, interaction: discord.Interaction, membro: discord.Member, motivo: str = "Não alinhado com a cultura."):
        """
        Expulsa (Kick) o usuário do servidor com mensagem temática.
        """
        # Verificações de segurança
        if membro.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode expulsar a si mesmo.", ephemeral=True)
            return

        if membro.top_role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Meu cargo não é alto o suficiente para expulsar este membro.", ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Expulsa o membro
            await membro.kick(reason=f"Choque de Realidade: {motivo}")

            # Mensagem pública temática
            await interaction.followup.send(
                f"🚪 **Choque de Realidade**\n\n"
                f"O usuário **{membro.display_name}** não estava pronto para a evolução e foi removido para buscar maturidade lá fora.\n"
                f"**Motivo:** {motivo}"
            )
            logger.info(f"{interaction.user} expulsou {membro} por: {motivo}")

        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para expulsar este usuário (verifique a hierarquia de cargos).")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao executar o comando: {str(e)}")
            logger.error(f"Erro no comando realidade: {e}")

    # Tratamento de erro local para permissões do comando
    @ego_check.error
    @realidade.error
    async def mod_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "🚫 **Autoridade Insuficiente.** Você precisa ser um Moderador ou Administrador para impor a realidade.", 
                ephemeral=True
            )
        else:
            logger.error(f"Erro não tratado em moderação: {error}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))