import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from bot.core.database import get_session
from bot.services.user_service import UserService

class Focus(commands.Cog):
    """
    Ferramenta de produtividade (Pomodoro).
    Ajuda os utilizadores a manterem o foco em tarefas e recompensa com XP.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Dicionário para rastrear quem está focado: {user_id: True}
        self.active_sessions = {}

    @app_commands.command(name="focar", description="Inicia um temporizador de foco e ganha XP ao terminar.")
    @app_commands.describe(minutos="Tempo de foco em minutos (min: 5, máx: 120)")
    async def focar(self, interaction: discord.Interaction, minutos: int):
        user_id = interaction.user.id

        # Validações Básicas
        if user_id in self.active_sessions:
            await interaction.response.send_message("❌ Já tens uma sessão de foco ativa! Termina essa primeiro.", ephemeral=True)
            return

        if minutos < 5 or minutos > 120:
            await interaction.response.send_message("⏱️ O tempo deve ser entre **5** e **120** minutos.", ephemeral=True)
            return

        # Calcula a recompensa (Ex: 5 XP por minuto focado)
        xp_reward = minutos * 5
        
        # Feedback inicial
        await interaction.response.send_message(
            f"🧘 **Modo Foco Ativado!**\n"
            f"⏲️ Temporizador definido para **{minutos} minutos**.\n"
            f"📵 Largue o telemóvel e foque na sua tarefa.\n"
            f"Eu avisarei quando acabar.",
            ephemeral=True # Mensagem privada para não poluir o chat
        )

        # Marca o utilizador como ocupado
        self.active_sessions[user_id] = True

        try:
            # Espera o tempo passar (conversão para segundos)
            # Nota: Se o bot reiniciar durante este tempo, o timer é perdido (limitação de memória)
            await asyncio.sleep(minutos * 60)
            
            # Verifica se ainda está na lista (caso tenhamos cancelado futuramente)
            if user_id in self.active_sessions:
                
                # Entrega a recompensa
                async with get_session() as session:
                    service = UserService(session)
                    leveled_up = await service.add_xp(user_id, xp_reward)
                    
                    # Mensagem de Conclusão
                    msg = (
                        f"🔔 **Tempo Esgotado!** {interaction.user.mention}\n"
                        f"✅ Sessão de {minutos} minutos concluída.\n"
                        f"💎 Ganhaste **{xp_reward} XP** pela tua disciplina."
                    )
                    
                    if leveled_up:
                        user_data = await service.get_profile(user_id)
                        msg += f"\n🏆 **SUBIU DE NÍVEL!** Agora és nível **{user_data.nivel}**."

                    # Tenta enviar DM, se falhar, manda no canal original (se possível) ou apenas remove da lista
                    try:
                        await interaction.user.send(msg)
                    except discord.Forbidden:
                        # Se DM fechada, tenta mandar no canal onde o comando foi usado (se ainda existir)
                        try:
                            await interaction.followup.send(msg, ephemeral=True)
                        except:
                            pass # Usuário sumiu ou canal deletado

        except Exception as e:
            # Garante que o utilizador é removido da lista se der erro
            pass
        finally:
            # Remove da lista de sessões ativas
            self.active_sessions.pop(user_id, None)

    @app_commands.command(name="foco_cancelar", description="Cancela o temporizador atual (sem recompensa).")
    async def foco_cancelar(self, interaction: discord.Interaction):
        if interaction.user.id in self.active_sessions:
            self.active_sessions.pop(interaction.user.id, None)
            await interaction.response.send_message("🛑 Sessão de foco cancelada. Nenhum XP foi atribuído.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Não tens nenhuma sessão ativa.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Focus(bot))