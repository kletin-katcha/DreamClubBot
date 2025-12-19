import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.challenge_service import ChallengeService
from bot.services.user_service import UserService

class Challenges(commands.Cog):
    """
    Sistema de Desafios Comunitários.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="desafio", description="Vê o desafio da semana ativo.")
    async def desafio(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            service = ChallengeService(session)
            challenge = await service.get_active_challenge()

        if not challenge:
            await interaction.followup.send("💤 Não há nenhum desafio ativo no momento. Fique atento aos anúncios!")
            return

        embed = discord.Embed(
            title=f"🔥 Desafio Ativo: {challenge.title}",
            description=challenge.description,
            color=discord.Color.red()
        )
        embed.add_field(name="Recompensa", value=f"💎 {challenge.xp_reward} XP")
        embed.set_footer(text=f"ID: {challenge.id} • Use /desafio_concluir quando terminar.")
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="desafio_concluir", description="Marca que completaste o desafio ativo.")
    async def desafio_concluir(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            chall_service = ChallengeService(session)
            user_service = UserService(session)

            challenge = await chall_service.get_active_challenge()
            if not challenge:
                await interaction.followup.send("❌ Não há desafios ativos para concluir.")
                return

            # Tenta completar
            is_new = await chall_service.complete_challenge(interaction.user.id, challenge.id)
            
            if not is_new:
                await interaction.followup.send("⚠️ Você já recebeu a recompensa deste desafio!")
                return

            # Dá o XP
            leveled_up = await user_service.add_xp(interaction.user.id, challenge.xp_reward)
            
            msg = f"✅ **Desafio Cumprido!**\nParabéns pela dedicação. Ganhaste **{challenge.xp_reward} XP**."
            if leveled_up:
                msg += "\n🏆 **LEVEL UP!**"

            await interaction.followup.send(msg)

    @app_commands.command(name="desafio_novo", description="[Admin] Cria um novo desafio para o servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def desafio_novo(self, interaction: discord.Interaction, titulo: str, descricao: str, xp: int = 200):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = ChallengeService(session)
            challenge = await service.create_challenge(titulo, descricao, xp)
        
        await interaction.followup.send(f"📢 **Novo Desafio Lançado!**\n**{challenge.title}**\n{challenge.description}\nRecompensa: {challenge.xp_reward} XP")

    @app_commands.command(name="desafio_encerrar", description="[Admin] Encerra o desafio ativo.")
    @app_commands.checks.has_permissions(administrator=True)
    async def desafio_encerrar(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = ChallengeService(session)
            challenge = await service.get_active_challenge()
            
            if challenge:
                await service.close_challenge(challenge.id)
                await interaction.followup.send(f"🔒 Desafio '{challenge.title}' encerrado com sucesso.")
            else:
                await interaction.followup.send("❌ Não encontrei nenhum desafio ativo.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Challenges(bot))