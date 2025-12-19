import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import logging
import re
from bot.config import settings
# Importa dos arquivos vizinhos na mesma pasta
from bot.cogs.music.views import TrackSelectView, PlayerControlView
from bot.cogs.music.utils import create_now_playing_embed

# Cores ANSI para o Terminal
class TermColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

logger = logging.getLogger(__name__)

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def setup_nodes(self):
        """Conecta aos nós do Lavalink (Multi-Node)."""
        await self.bot.wait_until_ready()
        
        if wavelink.Pool.nodes:
            return

        print(f"\n{TermColors.HEADER}--- INICIANDO SISTEMA DE ÁUDIO ---{TermColors.ENDC}")
        
        nodes_to_connect = []
        
        for node_cfg in settings.lavalink_nodes:
            identifier = node_cfg.get("identifier", "Unknown Node")
            uri = node_cfg["uri"]
            password = node_cfg["password"]
            
            print(f"{TermColors.CYAN}📡 Conectando a: {identifier}...{TermColors.ENDC}", end=" ")
            
            try:
                node = wavelink.Node(
                    identifier=identifier,
                    uri=uri,
                    password=password
                )
                nodes_to_connect.append(node)
                print(f"{TermColors.GREEN}[ONLINE] ✅{TermColors.ENDC}")
            except Exception as e:
                print(f"{TermColors.FAIL}[OFFLINE] ❌ ({e}){TermColors.ENDC}")

        if nodes_to_connect:
            await wavelink.Pool.connect(nodes=nodes_to_connect, client=self.bot, cache_capacity=100)
            print(f"{TermColors.GREEN}>>> ÁUDIO ONLINE: {len(nodes_to_connect)} nós ativos. <<<{TermColors.ENDC}\n")
        else:
            print(f"{TermColors.FAIL}>>> ALERTA: Nenhum servidor de música disponível! <<<{TermColors.ENDC}\n")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.setup_nodes()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player = payload.player
        if not player or not hasattr(player, "home_channel"):
            return
        
        embed = create_now_playing_embed(player)
        view = PlayerControlView(player)
        player.now_playing_msg = await player.home_channel.send(embed=embed, view=view)

    @app_commands.command(name="play", description="Toca música (Link ou Nome).")
    async def play(self, interaction: discord.Interaction, busca: str):
        # 1. Validação de Voz
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Você precisa estar em um canal de voz.", ephemeral=True)

        user_channel = interaction.user.voice.channel

        # --- PROTEÇÃO DE FROTA INTELIGENTE ---
        # Verifica se já existe OUTRO bot no mesmo canal.
        # Se existir, impedimos a conexão para evitar 2 bots gritando no mesmo ouvido.
        bots_in_channel = [m for m in user_channel.members if m.bot and m.id != self.bot.user.id]
        
        if bots_in_channel:
            other_bot = bots_in_channel[0]
            await interaction.response.send_message(
                f"🚫 **Canal Ocupado!**\n"
                f"O bot {other_bot.mention} já está neste canal.\n"
                f"Para evitar confusão, por favor use outro canal de voz ou use o comando `/play` no bot que já está lá.",
                ephemeral=True
            )
            return
        # -------------------------------------

        await interaction.response.defer()

        # 2. Conexão com o Canal
        if not interaction.guild.voice_client:
            try:
                player: wavelink.Player = await interaction.user.voice.channel.connect(cls=wavelink.Player)
                player.home_channel = interaction.channel
                player.autoplay = wavelink.AutoPlayMode.partial
            except Exception as e:
                return await interaction.followup.send("❌ Erro ao conectar. Verifique se há servidores de música online.")
        else:
            player = interaction.guild.voice_client
            # Garante que o bot está no mesmo canal que o usuário
            if player.channel.id != user_channel.id:
                 return await interaction.followup.send(f"❌ Eu já estou conectado em outro canal: {player.channel.mention}")

        # Busca Inteligente
        url_regex = re.compile(r'https?://(?:www\.)?.+')
        if url_regex.match(busca):
            tracks = await wavelink.Playable.search(busca)
        else:
            tracks = await wavelink.Playable.search(busca, source=wavelink.TrackSource.YouTube)

        if not tracks:
            return await interaction.followup.send("❌ Nada encontrado.")

        if isinstance(tracks, wavelink.Playlist):
            for t in tracks: t.requester = interaction.user
            await player.queue.put_wait(tracks)
            if not player.playing: await player.play(player.queue.get())
            await interaction.followup.send(f"✅ Playlist **{tracks.name}** adicionada.")
        
        elif url_regex.match(busca):
            track = tracks[0]
            track.requester = interaction.user
            await player.queue.put_wait(track)
            if not player.playing: await player.play(player.queue.get())
            await interaction.followup.send(f"✅ **{track.title}** adicionada.")

        else:
            view = TrackSelectView(tracks, player)
            await interaction.followup.send("🔎 **Selecione:**", view=view)

    @app_commands.command(name="pular", description="Pula a música.")
    async def pular(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if player and player.playing:
            await player.skip(force=True)
            await interaction.response.send_message("⏭️ Pulado!")
        else:
            await interaction.response.send_message("❌ Nada tocando.", ephemeral=True)

    @app_commands.command(name="parar", description="Desconecta.")
    async def parar(self, interaction: discord.Interaction):
        player = interaction.guild.voice_client
        if player:
            await player.disconnect()
            await interaction.response.send_message("👋 Player desligado.")
        else:
            await interaction.response.send_message("❌ Não estou conectado.", ephemeral=True)