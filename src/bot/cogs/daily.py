import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import random
from datetime import datetime, timedelta, time, timezone
from bot.core.database import get_session
from bot.services.user_service import UserService

logger = logging.getLogger(__name__)

QUOTES = [
    "“A felicidade de sua vida depende da qualidade de seus pensamentos.” – Marco Aurélio",
    "“Não é o que acontece com você, mas como você reage a isso que importa.” – Epicteto",
    "“Sorte é o que acontece quando a preparação encontra a oportunidade.” – Sêneca",
    "“O homem que move uma montanha começa carregando pequenas pedras.” – Confúcio",
    "“Nenhum homem é livre se não for mestre de si mesmo.” – Epicteto",
    "“Você tem poder sobre sua mente, não sobre eventos externos. Perceba isso e encontrará a força.” – Marco Aurélio",
    "“A disciplina é a ponte entre metas e realizações.” – Jim Rohn",
    "“Faça o que é certo, não o que é fácil.”",
]

class Daily(commands.Cog):
    """
    Cog responsável por rotinas diárias, recompensas e disciplina.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_channel_id = None
        self.daily_quote_loop.start()

    def cog_unload(self):
        self.daily_quote_loop.cancel()

    @tasks.loop(time=time(hour=9, minute=0, tzinfo=timezone.utc))
    async def daily_quote_loop(self):
        """Tarefa agendada para rodar todo dia às 09:00 UTC."""
        if self.daily_channel_id:
            channel = self.bot.get_channel(self.daily_channel_id)
            if channel:
                quote = random.choice(QUOTES)
                embed = discord.Embed(
                    title="☀️ Reflexão do Dia",
                    description=f"*{quote}*",
                    color=discord.Color.gold()
                )
                embed.set_footer(text="Mantenha a disciplina.")
                await channel.send(embed=embed)

    @app_commands.command(name="conselho", description="Receba uma pílula de sabedoria estoica agora.")
    async def conselho(self, interaction: discord.Interaction):
        quote = random.choice(QUOTES)
        embed = discord.Embed(
            title="🧘 Sabedoria",
            description=quote,
            color=discord.Color.light_grey()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setup_daily", description="Define este canal para receber as reflexões diárias.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_daily(self, interaction: discord.Interaction):
        self.daily_channel_id = interaction.channel_id
        await interaction.response.send_message(
            f"✅ **Configurado!** As reflexões diárias serão enviadas neste canal ({interaction.channel.mention}) às 09:00 UTC.",
            ephemeral=True
        )

    @app_commands.command(name="daily", description="Resgate sua recompensa diária (XP e DC$).")
    async def daily(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            # Garante que o usuário existe e traz os dados atualizados
            user = await service.get_or_create_user(interaction.user.id)
            
            now = datetime.utcnow()

            # Verifica Cooldown de 24h
            if user.last_daily:
                diff = now - user.last_daily
                if diff < timedelta(hours=24):
                    next_daily = user.last_daily + timedelta(hours=24)
                    timestamp = int(next_daily.timestamp())
                    await interaction.followup.send(f"⏳ **Calma, guerreiro!**\nVocê já treinou hoje. Volte <t:{timestamp}:R> para resgatar novamente.")
                    return

            # Recompensas Randomizadas (Valores Altos)
            xp_reward = random.randint(500, 1000)  # Muito XP (equivale a 25-50 mensagens)
            coins_reward = random.randint(100, 300) # Dinheiro para a loja

            # Aplica recompensas
            await service.add_xp(interaction.user.id, xp_reward)
            await service.add_coins(interaction.user.id, coins_reward)
            
            # Atualiza a data do daily
            user.last_daily = now
            session.add(user)
            await session.commit()

            # Feedback Visual
            embed = discord.Embed(
                title="☀️ Recompensa Diária Resgatada!",
                description="A consistência é a chave para a evolução.",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="Maturidade (XP)", value=f"+ **{xp_reward} XP** 📈", inline=True)
            embed.add_field(name="Fortuna (DC$)", value=f"+ **DC$ {coins_reward}** 💰", inline=True)
            
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Daily(bot))