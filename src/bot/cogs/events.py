import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.event_service import EventService
import datetime

class EventButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def update_event_message(self, interaction: discord.Interaction, event_id: int, service: EventService):
        """Atualiza a lista visual de participantes no embed."""
        going_ids = await service.get_participants(event_id, "going")
        maybe_ids = await service.get_participants(event_id, "maybe")
        
        # Formata listas (mentions)
        # Limita visualmente para não estourar o embed
        def format_list(ids):
            if not ids: return "Ninguém ainda."
            mentions = [f"<@{uid}>" for uid in ids]
            if len(mentions) > 10:
                return ", ".join(mentions[:10]) + f" e mais {len(mentions)-10}..."
            return ", ".join(mentions)

        # Recupera embed original
        message = interaction.message
        embed = message.embeds[0]
        
        # Atualiza campos (assume posições fixas ou busca por nome)
        # Vamos reconstruir os campos de status
        embed.clear_fields()
        embed.add_field(name=f"✅ Confirmados ({len(going_ids)})", value=format_list(going_ids), inline=False)
        embed.add_field(name=f"❔ Talvez ({len(maybe_ids)})", value=format_list(maybe_ids), inline=False)
        
        await message.edit(embed=embed)

    @discord.ui.button(label="Vou!", style=discord.ButtonStyle.success, custom_id="evt_going")
    async def going_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with get_session() as session:
            service = EventService(session)
            event = await service.get_event_by_message(interaction.message.id)
            if event:
                await service.add_participant(event.id, interaction.user.id, "going")
                await self.update_event_message(interaction, event.id, service)
                await interaction.followup.send("✅ Presença confirmada!", ephemeral=True)

    @discord.ui.button(label="Talvez", style=discord.ButtonStyle.secondary, custom_id="evt_maybe")
    async def maybe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with get_session() as session:
            service = EventService(session)
            event = await service.get_event_by_message(interaction.message.id)
            if event:
                await service.add_participant(event.id, interaction.user.id, "maybe")
                await self.update_event_message(interaction, event.id, service)
                await interaction.followup.send("❔ Marcado como 'Talvez'.", ephemeral=True)

    @discord.ui.button(label="Não Vou", style=discord.ButtonStyle.danger, custom_id="evt_not")
    async def not_going_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        async with get_session() as session:
            service = EventService(session)
            event = await service.get_event_by_message(interaction.message.id)
            if event:
                await service.remove_participant(event.id, interaction.user.id)
                await self.update_event_message(interaction, event.id, service)
                await interaction.followup.send("❌ Retirado da lista.", ephemeral=True)

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(EventButtons())

    @app_commands.command(name="evento_criar", description="Agenda um evento para a comunidade.")
    @app_commands.describe(titulo="Nome do evento", descricao="O que vai acontecer?", data="Data/Hora (Ex: 25/12 18:00)")
    async def evento_criar(self, interaction: discord.Interaction, titulo: str, descricao: str, data: str):
        # Tenta parsear a data (Formato Dia/Mês Hora:Minuto)
        try:
            # Adiciona o ano atual para facilitar
            current_year = datetime.datetime.now().year
            dt_str = f"{data}/{current_year}"
            start_time = datetime.datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
            # Se a data já passou este ano, assume próximo ano? (Simplificação: não)
        except ValueError:
            await interaction.response.send_message("❌ Formato de data inválido. Use: `DD/MM HH:MM` (Ex: 25/10 20:00).", ephemeral=True)
            return

        await interaction.response.defer()

        timestamp = int(start_time.timestamp())

        embed = discord.Embed(
            title=f"📅 {titulo}",
            description=f"{descricao}\n\n⏰ **Data:** <t:{timestamp}:F> (<t:{timestamp}:R>)",
            color=discord.Color.purple()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.add_field(name="✅ Confirmados (0)", value="Ninguém ainda.", inline=False)
        embed.add_field(name="❔ Talvez (0)", value="Ninguém ainda.", inline=False)
        embed.set_footer(text="Confirme sua presença abaixo.")

        message = await interaction.followup.send(embed=embed, view=EventButtons())

        async with get_session() as session:
            service = EventService(session)
            await service.create_event(
                interaction.guild.id,
                interaction.channel.id,
                message.id,
                interaction.user.id,
                titulo,
                descricao,
                start_time
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))