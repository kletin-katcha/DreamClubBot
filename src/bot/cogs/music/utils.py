import discord
import wavelink

def format_time(milliseconds: int) -> str:
    """Converte milissegundos para mm:ss."""
    if not milliseconds: return "00:00"
    seconds = milliseconds // 1000
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    return f"{int(minutes):02d}:{int(seconds):02d}"

def create_bar(current: int, total: int, length: int = 20, active_char="🔘", empty_char="▬") -> str:
    """Cria uma barra visual genérica (Progresso ou Volume)."""
    if total == 0:
        percent = 0
    else:
        percent = current / total
    
    filled = int(percent * length)
    filled = max(0, min(length, filled))
    return "▬" * filled + active_char + empty_char * (length - filled)

def create_now_playing_embed(player: wavelink.Player) -> discord.Embed:
    """Gera o Embed rico estilo Dashboard."""
    track = player.current
    if not track:
        return discord.Embed(title="⏹️ Player Parado", description="Adicione músicas com `/play`", color=discord.Color.dark_grey())

    # --- Configurações Visuais ---
    position = player.position
    duration = track.length
    
    # Barra de Progresso (Estilo YouTube)
    prog_bar = create_bar(position, duration, length=15)
    time_display = f"`{format_time(position)}` {prog_bar} `{format_time(duration)}`"

    # Barra de Volume (Visual)
    vol_bar = create_bar(player.volume, 100, length=5, active_char="🔊", empty_char="▪️")
    
    # Status de Loop
    loop_modes = {
        wavelink.QueueMode.normal: "Desativado",
        wavelink.QueueMode.loop: "🔂 Música",
        wavelink.QueueMode.loop_all: "🔁 Fila"
    }
    loop_text = loop_modes.get(player.queue.mode, "Desativado")

    # Próxima música (Spoiler)
    if not player.queue.is_empty:
        next_track = player.queue[0]
        next_text = f"**{next_track.title}**\n*{next_track.author}*"
    else:
        next_text = "*Fim da fila...*"

    # --- Montagem do Embed ---
    embed = discord.Embed(
        color=discord.Color.from_rgb(43, 45, 49) # Dark Discord Theme
    )
    
    # Cabeçalho: Status + Título
    status_icon = "⏸️" if player.paused else "▶️"
    embed.set_author(name=f"{status_icon} Tocando Agora", icon_url="https://i.imgur.com/S52164k.gif") # GIF de equalizador
    embed.title = track.title[:256]
    embed.url = track.uri
    embed.description = f"**Autor:** {track.author}\n\n{time_display}"

    # Bloco de Informações (Side-by-Side)
    embed.add_field(name="🎚️ Volume", value=f"{vol_bar} `{player.volume}%`", inline=True)
    embed.add_field(name="🔄 Loop", value=f"`{loop_text}`", inline=True)
    
    requester = getattr(track, "requester", None)
    req_mention = requester.mention if requester else "Sistema"
    embed.add_field(name="👤 Pedido por", value=req_mention, inline=True)
    
    # Próxima Música (Campo destacado)
    embed.add_field(name="⏭️ A Seguir", value=next_text, inline=False)

    if track.artwork:
        embed.set_thumbnail(url=track.artwork)
    
    return embed