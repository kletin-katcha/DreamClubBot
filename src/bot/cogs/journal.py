import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.journal_service import JournalService
from bot.services.user_service import UserService

class Journal(commands.Cog):
    """
    Sistema de Diário Pessoal (Journaling).
    Focado em reflexão e privacidade.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="diario_escrever", description="Escreva uma reflexão no seu diário privado.")
    @app_commands.describe(texto="Seu pensamento, lição ou vitória do dia.")
    async def diario_escrever(self, interaction: discord.Interaction, texto: str):
        # Resposta efêmera: Só você vê a mensagem de confirmação
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = JournalService(session)
            await service.add_entry(interaction.user.id, texto)
            
            # Recompensa o hábito da escrita com XP
            user_service = UserService(session)
            xp_amount = 50
            leveled_up = await user_service.add_xp(interaction.user.id, xp_amount)
            
        msg = f"✅ **Salvo!** Sua reflexão foi guardada com segurança no cofre.\n🧠 Ganhaste **{xp_amount} XP** por exercitar a mente."
        
        if leveled_up:
             msg += "\n🏆 **Evolução!** Você subiu de nível."

        await interaction.followup.send(msg)

    @app_commands.command(name="diario_ler", description="Envia suas últimas 5 anotações para sua DM (Privado).")
    async def diario_ler(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = JournalService(session)
            entries = await service.get_user_entries(interaction.user.id)
            
        if not entries:
            await interaction.followup.send("📭 Seu diário está vazio. Use `/diario_escrever` para começar.")
            return

        # Tenta enviar na DM para privacidade total
        try:
            embed = discord.Embed(
                title="📔 Seu Diário Pessoal", 
                description="Aqui estão suas últimas reflexões:",
                color=discord.Color.dark_grey()
            )
            
            for entry in entries:
                # Formata a data (Dia/Mês Hora:Minuto)
                data = entry.created_at.strftime("%d/%m %H:%M")
                # Corta o texto se for muito grande para caber no embed
                texto_preview = (entry.content[:200] + '...') if len(entry.content) > 200 else entry.content
                
                embed.add_field(
                    name=f"📅 {data}", 
                    value=f"_{texto_preview}_", 
                    inline=False
                )
            
            embed.set_footer(text="Apenas você tem acesso a isso.")
            await interaction.user.send(embed=embed)
            await interaction.followup.send("✅ Enviei suas anotações para sua Mensagem Direta (DM).")
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Não consegui enviar DM. Por favor, libere suas mensagens diretas nas configurações do servidor.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Journal(bot))