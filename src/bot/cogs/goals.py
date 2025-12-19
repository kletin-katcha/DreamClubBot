import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.goal_service import GoalService
from bot.services.user_service import UserService

class Goals(commands.Cog):
    """
    Gerenciamento de objetivos e metas pessoais.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="meta_nova", description="Defina um novo objetivo para hoje.")
    @app_commands.describe(descricao="Qual é o seu objetivo? (Ex: Ler 10 páginas)")
    async def meta_nova(self, interaction: discord.Interaction, descricao: str):
        if len(descricao) > 200:
            await interaction.response.send_message("❌ Mantenha a meta curta (máx 200 caracteres).", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = GoalService(session)
            goal = await service.add_goal(interaction.user.id, descricao)

        await interaction.followup.send(f"✅ **Meta Definida!** ID: `{goal.id}`\n🎯 *{goal.description}*\nUse `/meta_concluir {goal.id}` quando terminar.")

    @app_commands.command(name="metas", description="Lista seus objetivos pendentes.")
    async def metas(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = GoalService(session)
            goals = await service.list_pending_goals(interaction.user.id)

        if not goals:
            await interaction.followup.send("🎉 Você não tem metas pendentes! Use `/meta_nova` para criar uma.")
            return

        embed = discord.Embed(title=f"📋 Metas de {interaction.user.display_name}", color=discord.Color.orange())
        description = ""
        for goal in goals:
            description += f"**#{goal.id}** - {goal.description}\n"
        
        embed.description = description
        embed.set_footer(text="Foco no processo.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="meta_concluir", description="Marca uma meta como feita e ganha XP.")
    @app_commands.describe(id_meta="O número (ID) da meta que você completou (veja em /metas)")
    async def meta_concluir(self, interaction: discord.Interaction, id_meta: int):
        await interaction.response.defer()

        async with get_session() as session:
            goal_service = GoalService(session)
            user_service = UserService(session) # Precisamos disto para dar o XP

            # Tenta concluir a meta
            completed_goal = await goal_service.complete_goal(id_meta, interaction.user.id)

            if not completed_goal:
                await interaction.followup.send(f"❌ Meta #{id_meta} não encontrada ou já concluída.")
                return

            # Recompensa: 100 XP por meta cumprida!
            xp_reward = 100
            leveled_up = await user_service.add_xp(interaction.user.id, xp_reward)

            msg = f"✅ **Meta Concluída!**\n~~{completed_goal.description}~~\n💎 Ganhaste **{xp_reward} XP** pela disciplina."
            
            if leveled_up:
                user_data = await user_service.get_profile(interaction.user.id)
                msg += f"\n🏆 **LEVEL UP!** Parabéns, agora és nível **{user_data.nivel}**!"

            await interaction.followup.send(msg)

async def setup(bot: commands.Bot):
    await bot.add_cog(Goals(bot))