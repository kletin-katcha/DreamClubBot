import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.core.database import get_session
from bot.services.giveaway_service import GiveawayService
import datetime
import random
import asyncio

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Botão eterno

    @discord.ui.button(label="Participar 🎉", style=discord.ButtonStyle.success, custom_id="gw_join_btn")
    async def join_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apenas responde para dar feedback visual, a "inscrição" é estar na lista de interações da mensagem
        await interaction.response.send_message("✅ Você está participando do sorteio! Boa sorte.", ephemeral=True)

class Giveaways(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        """Verifica periodicamente se algum sorteio chegou ao fim."""
        # Aguarda o bot estar pronto para evitar erros de cache
        await self.bot.wait_until_ready()

        async with get_session() as session:
            service = GiveawayService(session)
            active_gws = await service.get_active_giveaways()

            for gw in active_gws:
                if datetime.datetime.utcnow() >= gw.end_time:
                    # O tempo acabou! Vamos sortear.
                    await self.roll_winner(gw, session)

    async def roll_winner(self, gw, session):
        """Realiza o sorteio e anuncia o vencedor."""
        try:
            channel = self.bot.get_channel(gw.channel_id)
            if not channel:
                # Tenta buscar (fetch) se não estiver no cache
                try:
                    channel = await self.bot.fetch_channel(gw.channel_id)
                except:
                    # Canal deletado? Marca como encerrado para parar de tentar
                    service = GiveawayService(session)
                    await service.end_giveaway(gw.message_id)
                    return

            try:
                message = await channel.fetch_message(gw.message_id)
            except:
                # Mensagem deletada?
                service = GiveawayService(session)
                await service.end_giveaway(gw.message_id)
                return

            # Pega quem interagiu com a mensagem (Botão ou Reações)
            # Como usamos botão, precisamos pegar quem interagiu. 
            # Infelizmente, a API do Discord não lista fácil quem clicou num botão passado.
            # SOLUÇÃO SIMPLES: Vamos usar Reação 🎉 para sortear, é mais seguro para persistência.
            
            # Vamos buscar as reações da mensagem
            reaction = discord.utils.get(message.reactions, emoji="🎉")
            
            users = []
            if reaction:
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)

            service = GiveawayService(session)
            await service.end_giveaway(gw.message_id)

            if not users:
                await channel.send(f"⚠️ **Sorteio Encerrado:** {gw.prize}\nNinguém participou. 😢")
                return

            # Sorteia
            winner_count = min(len(users), gw.winners_count)
            winners = random.sample(users, winner_count)
            winners_mention = ", ".join([w.mention for w in winners])

            embed = discord.Embed(
                title="🎉 TEMOS UM VENCEDOR!",
                description=f"**Prémio:** {gw.prize}\n**Ganhador(es):** {winners_mention}",
                color=discord.Color.gold()
            )
            embed.set_footer(text="Parabéns! Abra um ticket para resgatar.")
            
            await channel.send(content=f"🎉 Parabéns {winners_mention}!", embed=embed)
            
            # Edita a mensagem original para dizer ENCERRADO
            original_embed = message.embeds[0]
            original_embed.color = discord.Color.dark_grey()
            original_embed.set_footer(text="🔴 Sorteio Encerrado")
            await message.edit(embed=original_embed, view=None)

        except Exception as e:
            print(f"Erro ao finalizar sorteio {gw.id}: {e}")

    @app_commands.command(name="sorteio_criar", description="[Admin] Inicia um novo sorteio.")
    @app_commands.describe(premio="O que será sorteado", duracao="Duração (ex: 10m, 1h, 24h)", vencedores="Quantas pessoas ganham")
    @app_commands.checks.has_permissions(administrator=True)
    async def sorteio_criar(self, interaction: discord.Interaction, premio: str, duracao: str, vencedores: int = 1):
        # Parse da duração simples
        seconds = 0
        unit = duracao[-1].lower()
        value = int(duracao[:-1])
        
        if unit == 's': seconds = value
        elif unit == 'm': seconds = value * 60
        elif unit == 'h': seconds = value * 3600
        elif unit == 'd': seconds = value * 86400
        else:
            await interaction.response.send_message("❌ Formato de tempo inválido. Use s/m/h/d (ex: 30m, 2h).", ephemeral=True)
            return

        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)
        end_timestamp = int(end_time.timestamp()) # Para mostrar no Discord <t:TIMESTAMP:R>

        embed = discord.Embed(
            title="🎉 SORTEIO INICIADO! 🎉",
            description=f"**Prémio:** {premio}\n\n"
                        f"⏰ **Termina:** <t:{end_timestamp}:R>\n"
                        f"🏆 **Vencedores:** {vencedores}\n\n"
                        f"**Reaja com 🎉 para participar!**",
            color=discord.Color.purple()
        )
        
        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        await message.add_reaction("🎉")

        async with get_session() as session:
            service = GiveawayService(session)
            await service.create_giveaway(
                interaction.guild.id,
                interaction.channel.id,
                message.id,
                premio,
                end_time,
                vencedores
            )

    @app_commands.command(name="sorteio_encerrar", description="[Admin] Encerra um sorteio imediatamente.")
    @app_commands.describe(id_mensagem="ID da mensagem do sorteio")
    @app_commands.checks.has_permissions(administrator=True)
    async def sorteio_encerrar(self, interaction: discord.Interaction, id_mensagem: str):
        await interaction.response.defer(ephemeral=True)
        
        try:
            msg_id = int(id_mensagem)
        except:
            await interaction.followup.send("❌ ID inválido.")
            return

        async with get_session() as session:
            service = GiveawayService(session)
            # Verifica se existe
            stmt = select(Giveaway).where(Giveaway.message_id == msg_id, Giveaway.active == True)
            gw = (await session.execute(stmt)).scalar_one_or_none()
            
            if not gw:
                await interaction.followup.send("❌ Sorteio não encontrado ou já encerrado.")
                return

            # Força o encerramento manual
            await self.roll_winner(gw, session)
            await interaction.followup.send("✅ Sorteio encerrado manualmente.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))