import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.level_service import LevelService

class LevelRewards(commands.Cog):
    """
    Gerencia a entrega automática de cargos por nível.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="config_nivel_premio", description="[Admin] Define um cargo para quem atingir X nível.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_reward(self, interaction: discord.Interaction, nivel: int, cargo: discord.Role):
        if cargo >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ Esse cargo é superior ao meu. Não poderei entregá-lo.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = LevelService(session)
            await service.add_reward(interaction.guild.id, nivel, cargo.id)

        await interaction.followup.send(f"✅ Configurado! Quem atingir o **Nível {nivel}** ganhará o cargo **{cargo.name}**.")

    @app_commands.command(name="config_nivel_lista", description="[Admin] Lista as recompensas configuradas.")
    @app_commands.checks.has_permissions(administrator=True)
    async def list_rewards(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            service = LevelService(session)
            rewards = await service.get_all_rewards(interaction.guild.id)

        if not rewards:
            await interaction.followup.send("📭 Nenhuma recompensa de nível configurada.")
            return

        description = ""
        for r in rewards:
            role = interaction.guild.get_role(r.role_id)
            role_name = role.mention if role else "`Cargo Deletado`"
            description += f"🏆 **Nível {r.level_required}:** {role_name}\n"

        embed = discord.Embed(title="🎖️ Recompensas de Nível", description=description, color=discord.Color.gold())
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="config_nivel_remover", description="[Admin] Remove uma recompensa.")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_reward(self, interaction: discord.Interaction, nivel: int):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = LevelService(session)
            success = await service.remove_reward(interaction.guild.id, nivel)

        if success:
            await interaction.followup.send(f"🗑️ Recompensa do Nível {nivel} removida.")
        else:
            await interaction.followup.send("❌ Nenhuma recompensa encontrada para esse nível.")

async def setup(bot: commands.Bot):
    await bot.add_cog(LevelRewards(bot))