import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.mentorship_service import MentorshipService

class MentorshipCog(commands.Cog):
    """
    Sistema de Mestre e Aprendiz.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="mentor_convidar", description="[Nível 5+] Convida um iniciante para ser seu aprendiz.")
    async def mentor_convidar(self, interaction: discord.Interaction, membro: discord.Member):
        if membro.id == interaction.user.id or membro.bot:
            await interaction.response.send_message("❌ Convite inválido.", ephemeral=True)
            return

        await interaction.response.defer()

        async with get_session() as session:
            service = MentorshipService(session)
            # Tenta criar o vínculo
            success, msg = await service.create_mentorship(interaction.user.id, membro.id)

        if success:
            await interaction.followup.send(f"🤝 **Nova Aliança!**\n{interaction.user.mention} agora é o mentor de {membro.mention}.\n*Guie-o com sabedoria.*")
        else:
            await interaction.followup.send(f"❌ {msg}")

    @app_commands.command(name="mentoria_encerrar", description="Rompe o vínculo com seu mentor/aprendiz.")
    async def mentoria_encerrar(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = MentorshipService(session)
            # Tenta encerrar (assume que quem chama é o aprendiz, lógica simplificada)
            # Num sistema real, verificaríamos ambos os lados
            success = await service.end_mentorship(interaction.user.id)
            
        if success:
            await interaction.followup.send("💔 Vínculo de mentoria encerrado. Siga seu próprio caminho.")
        else:
            await interaction.followup.send("❌ Você não é um aprendiz ativo.")

async def setup(bot: commands.Bot):
    await bot.add_cog(MentorshipCog(bot))