import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.guild_service import GuildService
import logging

logger = logging.getLogger(__name__)

class VoiceMaster(commands.Cog):
    """
    Sistema de canais de voz temporários (Join to Create).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """
        Monitoriza mudanças de canal de voz.
        1. Se entrou no Hub -> Cria sala e move.
        2. Se saiu de uma sala temporária vazia -> Apaga.
        """
        # Ignora bots
        if member.bot:
            return

        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(member.guild.id)

        # Se não houver config de voz, ignora
        if not config.voice_hub_id or not config.voice_category_id:
            return

        # --- CASO 1: CRIAR SALA (Entrou no Hub) ---
        if after.channel and after.channel.id == config.voice_hub_id:
            guild = member.guild
            category = guild.get_channel(config.voice_category_id)

            if category:
                # Permissões: O dono da sala tem controlo total
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(connect=True),
                    member: discord.PermissionOverwrite(move_members=True, manage_channels=True, connect=True)
                }
                
                try:
                    # Cria o canal
                    channel_name = f"🔊 Sala de {member.display_name}"
                    new_channel = await guild.create_voice_channel(
                        name=channel_name, 
                        category=category,
                        overwrites=overwrites
                    )
                    
                    # Move o membro para lá
                    await member.move_to(new_channel)
                    logger.info(f"Sala de voz criada para {member.display_name}")
                except discord.Forbidden:
                    logger.warning(f"Sem permissão para criar/mover em {guild.name}")
                except Exception as e:
                    logger.error(f"Erro ao criar sala de voz: {e}")

        # --- CASO 2: APAGAR SALA (Saiu e ficou vazia) ---
        if before.channel:
            # Verifica se o canal que ele saiu faz parte da categoria dinâmica
            if before.channel.category_id == config.voice_category_id:
                # E se NÃO for o canal Hub principal (não queremos apagar o gerador)
                if before.channel.id != config.voice_hub_id:
                    # Se estiver vazio (0 membros humanos)
                    if len(before.channel.members) == 0:
                        try:
                            await before.channel.delete()
                            logger.info(f"Sala vazia apagada: {before.channel.name}")
                        except discord.Forbidden:
                            pass
                        except Exception as e:
                            logger.error(f"Erro ao apagar sala: {e}")

    @app_commands.command(name="setup_voice", description="[Admin] Cria a categoria e o canal de 'Criar Sala'.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_voice(self, interaction: discord.Interaction):
        await interaction.response.defer()

        guild = interaction.guild
        
        try:
            # 1. Cria a Categoria
            category = await guild.create_category("🔊 Hub de Voz")
            
            # 2. Cria o Canal Gatilho
            hub_channel = await guild.create_voice_channel("➕ Criar Sala", category=category)
            
            # 3. Salva no Banco
            async with get_session() as session:
                service = GuildService(session)
                await service.set_voice_hub(guild.id, hub_channel.id, category.id)
            
            embed = discord.Embed(
                title="✅ Configuração Concluída",
                description=f"O sistema de voz foi criado!\n\n"
                            f"📂 Categoria: **{category.name}**\n"
                            f"🔊 Canal Gerador: **{hub_channel.name}**\n\n"
                            f"Agora, quem entrar no canal '➕ Criar Sala' terá uma sala privada criada automaticamente.",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ Não tenho permissão para criar canais (Manage Channels).")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro desconhecido: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceMaster(bot))