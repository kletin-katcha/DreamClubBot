import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.user_service import UserService

class Ranking(commands.Cog):
    """
    Sistema de Leaderboard para exibir os membros mais evoluídos.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ranking", description="Veja o Top 10 membros com maior maturidade.")
    async def ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            top_users = await service.get_leaderboard(limit=10)

        if not top_users:
            await interaction.followup.send("Ainda não há dados suficientes para o ranking.")
            return

        embed = discord.Embed(
            title="🏆 Ranking de Maturidade",
            description="Aqueles que buscam a evolução constante.",
            color=discord.Color.gold()
        )

        medals = ["🥇", "🥈", "🥉"]
        
        for index, user_data in enumerate(top_users):
            # Tenta pegar o nome do membro no servidor
            member = interaction.guild.get_member(user_data.id)
            name = member.display_name if member else f"Utilizador {user_data.id}"
            
            # Define o ícone da posição (medalha ou número)
            rank_icon = medals[index] if index < 3 else f"`#{index + 1}`"
            
            embed.add_field(
                name=f"{rank_icon} {name}",
                value=f"Nível: **{user_data.nivel}** | XP: *{user_data.xp_maturidade}*",
                inline=False
            )

        embed.set_footer(text="Continue focado no seu progresso.")
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ranking(bot))