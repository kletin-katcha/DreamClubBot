import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.guild_service import GuildService
from bot.services.ticket_service import TicketService
import logging

logger = logging.getLogger(__name__)

# --- View Persistente para Abrir Ticket ---
class TicketLauncher(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout None = Botão eterno

    @discord.ui.button(label="Abrir Atendimento", style=discord.ButtonStyle.primary, emoji="📩", custom_id="ticket_open_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            guild_service = GuildService(session)
            config = await guild_service.get_config(interaction.guild.id)
            
            if not config.ticket_category_id:
                await interaction.followup.send("❌ O sistema de tickets não está configurado. Contacte um admin.")
                return

            category = interaction.guild.get_channel(config.ticket_category_id)
            if not category:
                await interaction.followup.send("❌ Categoria de tickets não encontrada.")
                return

            # Verifica se já tem ticket aberto (opcional, evita spam)
            # Para simplificar, vamos permitir múltiplos por agora

            # Cria o Canal
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            
            channel_name = f"ticket-{interaction.user.name}"
            ticket_channel = await interaction.guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            
            # Regista no Banco
            ticket_service = TicketService(session)
            await ticket_service.create_ticket(interaction.guild.id, ticket_channel.id, interaction.user.id)

        # Envia painel de controlo dentro do ticket
        embed = discord.Embed(
            title=f"Atendimento: {interaction.user.display_name}",
            description="Descreva o seu problema. A equipa responderá em breve.",
            color=discord.Color.green()
        )
        await ticket_channel.send(f"{interaction.user.mention}", embed=embed, view=TicketControls())
        
        await interaction.followup.send(f"✅ Ticket criado: {ticket_channel.mention}")

# --- View de Controlo (Fechar Ticket) ---
class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="ticket_close_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = TicketService(session)
            await service.close_ticket(interaction.channel.id)

        await interaction.channel.send("🔒 Este ticket será apagado em 5 segundos...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # Regista as views persistentes ao iniciar o bot para os botões funcionarem após reinício
    async def cog_load(self):
        self.bot.add_view(TicketLauncher())
        self.bot.add_view(TicketControls())

    @app_commands.command(name="setup_tickets", description="[Admin] Cria o painel de suporte.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_tickets(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        guild = interaction.guild
        
        # 1. Cria Categoria
        try:
            category = await guild.create_category("📩 Suporte")
            
            # 2. Salva Config
            async with get_session() as session:
                service = GuildService(session)
                await service.set_ticket_category(guild.id, category.id)

            # 3. Envia Painel
            embed = discord.Embed(
                title="Central de Ajuda",
                description="Precisa de falar com a moderação? Clique no botão abaixo para abrir um atendimento privado.",
                color=discord.Color.blurple()
            )
            embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            
            await interaction.channel.send(embed=embed, view=TicketLauncher())
            await interaction.followup.send("✅ Sistema de tickets configurado!")

        except discord.Forbidden:
            await interaction.followup.send("❌ Sem permissão para criar categorias/canais.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))