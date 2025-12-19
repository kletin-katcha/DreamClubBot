import discord
from discord import app_commands
from discord.ext import commands, tasks
from bot.core.database import get_session
from bot.services.stats_service import StatsService
import datetime

class ServerStats(commands.Cog):
    """
    Mantém os contadores do servidor atualizados.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.update_stats_loop.start()

    def cog_unload(self):
        self.update_stats_loop.cancel()

    @tasks.loop(minutes=10)
    async def update_stats_loop(self):
        """Atualiza os nomes dos canais periodicamente."""
        await self.bot.wait_until_ready()

        async with get_session() as session:
            service = StatsService(session)
            
            # Itera sobre todos os servidores que o bot está
            for guild in self.bot.guilds:
                stats = await service.get_guild_stats(guild.id)
                
                # Dados frescos
                member_count = guild.member_count
                # Conta online (pode ser lento em servidores gigantes)
                online_count = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
                bot_count = sum(1 for m in guild.members if m.bot)
                human_count = member_count - bot_count
                date_str = datetime.datetime.utcnow().strftime("%d/%m")

                for stat in stats:
                    channel = guild.get_channel(stat.channel_id)
                    if not channel:
                        # Se o canal foi deletado manualmente, remove do banco
                        await service.remove_stat(stat.channel_id)
                        continue

                    # Define o valor baseado no tipo
                    val = 0
                    if stat.stat_type == 'members': val = member_count
                    elif stat.stat_type == 'humans': val = human_count
                    elif stat.stat_type == 'online': val = online_count
                    elif stat.stat_type == 'bots': val = bot_count
                    elif stat.stat_type == 'date': val = date_str

                    # Formata o nome (Ex: "👥 Membros: 500")
                    try:
                        new_name = stat.name_format.replace("{count}", str(val))
                        # Só edita se mudou (para evitar rate limit)
                        if channel.name != new_name:
                            await channel.edit(name=new_name)
                    except Exception as e:
                        print(f"Erro ao atualizar stat {stat.id}: {e}")

    @app_commands.command(name="setup_stats", description="[Admin] Cria painel de estatísticas no topo do servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild = interaction.guild

        try:
            # Cria Categoria
            category = await guild.create_category("📊 Estatísticas", position=0)
            
            # Define permissões (Ninguém pode conectar/falar, apenas ver)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False, view_channel=True)
            }

            # Configurações padrão
            configs = [
                ("👥 Membros: {count}", "members"),
                ("🟢 Online: {count}", "online"),
                ("📅 Data: {count}", "date")
            ]

            async with get_session() as session:
                service = StatsService(session)
                
                for fmt, stype in configs:
                    # Cria canal de voz (visual)
                    chan = await guild.create_voice_channel(name=fmt.format(count="..."), category=category, overwrites=overwrites)
                    # Salva no banco
                    await service.create_stat_entry(guild.id, chan.id, stype, fmt)

            await interaction.followup.send("✅ **Contadores criados!** Eles serão atualizados em alguns minutos.")
            # Força update inicial
            await self.update_stats_loop()

        except discord.Forbidden:
            await interaction.followup.send("❌ Preciso de permissão 'Manage Channels' para criar estatísticas.")

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerStats(bot))