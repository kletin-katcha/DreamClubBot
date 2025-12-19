import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.core.database import get_session
from bot.services.reminder_service import ReminderService
import datetime

class Reminders(commands.Cog):
    """
    Sistema de alertas e produtividade.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Verifica a cada 30 segundos se há lembretes para entregar."""
        await self.bot.wait_until_ready()

        async with get_session() as session:
            service = ReminderService(session)
            due_list = await service.get_due_reminders()

            for reminder in due_list:
                try:
                    # Tenta pegar o canal (ou DM)
                    channel = self.bot.get_channel(reminder.channel_id)
                    if not channel:
                        try:
                            # Se for DM e não estiver no cache
                            user = await self.bot.fetch_user(reminder.user_id)
                            channel = await user.create_dm()
                        except:
                            pass # Falha na entrega
                    
                    if channel:
                        embed = discord.Embed(
                            title="⏰ Lembrete!",
                            description=f"**Você pediu para lembrar:**\n\n📝 {reminder.message}",
                            color=discord.Color.teal(),
                            timestamp=reminder.created_at
                        )
                        embed.set_footer(text="Definido em")
                        await channel.send(content=f"<@{reminder.user_id}>", embed=embed)
                    
                except Exception as e:
                    print(f"Erro ao entregar lembrete {reminder.id}: {e}")
                finally:
                    # Marca como completo para não repetir
                    await service.complete_reminder(reminder.id)

    @app_commands.command(name="lembrete", description="Define um alerta para o futuro.")
    @app_commands.describe(tempo="Daqui a quanto tempo? (ex: 10m, 1h, 30s)", mensagem="O que devo lembrar?")
    async def lembrete(self, interaction: discord.Interaction, tempo: str, mensagem: str):
        # Lógica simples de parsing de tempo (Igual ao sorteio)
        seconds = 0
        unit = tempo[-1].lower()
        
        try:
            value = int(tempo[:-1])
        except ValueError:
             await interaction.response.send_message("❌ Formato inválido. Use números seguidos de s/m/h (ex: 30m).", ephemeral=True)
             return

        if unit == 's': seconds = value
        elif unit == 'm': seconds = value * 60
        elif unit == 'h': seconds = value * 3600
        elif unit == 'd': seconds = value * 86400
        else:
            await interaction.response.send_message("❌ Unidade inválida. Use s (segundos), m (minutos), h (horas) ou d (dias).", ephemeral=True)
            return

        if seconds < 10:
            await interaction.response.send_message("❌ O tempo mínimo é de 10 segundos.", ephemeral=True)
            return

        due_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        timestamp = int(due_at.timestamp())

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = ReminderService(session)
            # Salva o ID do canal atual para responder aqui mesmo.
            # Se quiseres forçar DM, podes usar interaction.user.dm_channel.id (se existir)
            await service.create_reminder(
                interaction.user.id,
                interaction.channel_id,
                mensagem,
                due_at
            )

        await interaction.followup.send(f"✅ **Lembrete definido!**\nVou te avisar sobre *'{mensagem}'* <t:{timestamp}:R>.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))