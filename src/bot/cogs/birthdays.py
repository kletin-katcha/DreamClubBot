import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import time, timezone, date
from bot.core.database import get_session
from bot.services.birthday_service import BirthdayService
from bot.services.guild_service import GuildService
from bot.services.user_service import UserService

class Birthdays(commands.Cog):
    """
    Sistema de celebração de aniversários.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    @tasks.loop(time=time(hour=8, minute=0, tzinfo=timezone.utc)) # Roda às 08:00 UTC
    async def check_birthdays(self):
        """Verifica aniversariantes e envia parabéns."""
        await self.bot.wait_until_ready()

        async with get_session() as session:
            # Busca aniversariantes
            bd_service = BirthdayService(session)
            birthdays = await bd_service.get_todays_birthdays()
            
            if not birthdays:
                return

            # Para cada servidor que o bot está
            for guild in self.bot.guilds:
                # Busca configuração de canal (usaremos o chat geral/boas-vindas como fallback ou um específico)
                guild_service = GuildService(session)
                config = await guild_service.get_config(guild.id)
                
                # Tenta usar o canal de boas-vindas para dar parabéns se não houver um específico
                target_channel_id = config.welcome_channel_id 
                
                if not target_channel_id:
                    continue

                channel = guild.get_channel(target_channel_id)
                if not channel:
                    continue

                # Filtra aniversariantes que estão neste servidor
                mentions = []
                user_service = UserService(session)
                
                for bd in birthdays:
                    member = guild.get_member(bd.user_id)
                    if member:
                        mentions.append(member.mention)
                        # Presente de aniversário: 500 XP!
                        await user_service.add_xp(member.id, 500)

                if mentions:
                    mentions_str = ", ".join(mentions)
                    embed = discord.Embed(
                        title="🎉 Feliz Aniversário! 🎂",
                        description=f"Hoje é um dia especial no Dream Club!\n\n"
                                    f"Parabéns a {mentions_str} por mais um ano de vida e evolução.\n"
                                    f"🎁 **Presente:** Ganharam **500 XP** de bónus!",
                        color=discord.Color.fuchsia()
                    )
                    embed.set_image(url="https://i.imgur.com/0v8X9Lp.gif") # GIF de festa
                    await channel.send(content=f"Parabéns {mentions_str}! 🥳", embed=embed)

    @app_commands.command(name="aniversario", description="Define a sua data de aniversário.")
    @app_commands.describe(dia="Dia (1-31)", mes="Mês (1-12)")
    async def aniversario(self, interaction: discord.Interaction, dia: int, mes: int):
        # Validação simples
        try:
            # Tenta criar uma data (ano bissexto 2000 para permitir 29/02)
            date(2000, mes, dia)
        except ValueError:
            await interaction.response.send_message("❌ Data inválida.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = BirthdayService(session)
            await service.set_birthday(interaction.user.id, dia, mes)

        await interaction.followup.send(f"✅ Aniversário definido para **{dia:02d}/{mes:02d}**. Vou lembrar-me!")

    @app_commands.command(name="aniversariantes", description="Vê quem faz anos hoje.")
    async def aniversariantes(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = BirthdayService(session)
            bds = await service.get_todays_birthdays()
            
        if not bds:
            await interaction.followup.send("📅 Ninguém faz anos hoje.")
            return
            
        names = []
        for bd in bds:
            member = interaction.guild.get_member(bd.user_id)
            if member:
                names.append(member.display_name)
                
        if names:
            await interaction.followup.send(f"🎂 **Aniversariantes de Hoje:** {', '.join(names)}")
        else:
            await interaction.followup.send("📅 Ninguém deste servidor faz anos hoje.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Birthdays(bot))