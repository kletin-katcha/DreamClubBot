import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.habit_service import HabitService
from bot.services.user_service import UserService

class Habits(commands.Cog):
    """
    Sistema de rastreio de hábitos e sequências (Streaks).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="habito_novo", description="Cria um novo hábito para monitorizar.")
    @app_commands.describe(nome="Nome do hábito (ex: Banho Gelado, Leitura)")
    async def habito_novo(self, interaction: discord.Interaction, nome: str):
        if len(nome) > 50:
            await interaction.response.send_message("❌ O nome deve ser curto (máx 50 caracteres).", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = HabitService(session)
            habit = await service.create_habit(interaction.user.id, nome)

        await interaction.followup.send(f"✅ Hábito **{habit.name}** criado! ID: `{habit.id}`. Não te esqueças de fazer `/checkin` diariamente.")

    @app_commands.command(name="habitos", description="Vê os teus hábitos e sequências atuais.")
    async def habitos(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = HabitService(session)
            habits = await service.list_user_habits(interaction.user.id)

        if not habits:
            await interaction.followup.send("Não tens hábitos registados. Usa `/habito_novo`.")
            return

        embed = discord.Embed(title="📅 Teus Hábitos", color=discord.Color.blue())
        
        for habit in habits:
            status = "🔥" if habit.current_streak > 2 else "🌱"
            embed.add_field(
                name=f"{status} {habit.name} (ID: {habit.id})",
                value=f"Sequência Atual: **{habit.current_streak}** dias\nRecorde: {habit.longest_streak} dias",
                inline=False
            )
        
        embed.set_footer(text="A consistência é a chave.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="checkin", description="Marca que realizaste o hábito hoje.")
    @app_commands.describe(habit_id="O ID do hábito (vê em /habitos)")
    async def checkin(self, interaction: discord.Interaction, habit_id: int):
        await interaction.response.defer()

        async with get_session() as session:
            habit_service = HabitService(session)
            user_service = UserService(session)
            
            success, msg, habit = await habit_service.check_in(habit_id, interaction.user.id)

            if not success:
                await interaction.followup.send(f"❌ {msg}")
                return

            # Recompensa por consistência: 50 XP base + Bónus por Streak
            xp_bonus = min(habit.current_streak * 5, 100) # Máximo 100 XP extra
            total_xp = 50 + xp_bonus
            
            leveled_up = await user_service.add_xp(interaction.user.id, total_xp)

            response = f"✅ **Check-in realizado!** ({habit.name})\n{msg}\n💎 Ganhaste **{total_xp} XP**."
            
            if leveled_up:
                 response += "\n🏆 **SUBIU DE NÍVEL!**"

            await interaction.followup.send(response)

async def setup(bot: commands.Bot):
    await bot.add_cog(Habits(bot))