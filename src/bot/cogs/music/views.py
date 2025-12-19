
import discord
import wavelink
from bot.cogs.music.utils import create_now_playing_embed

class TrackSelect(discord.ui.Select):
    """Menu de Seleção de Música (Busca)."""
    def __init__(self, tracks: list[wavelink.Playable], player: wavelink.Player):
        self.player = player
        self.tracks_ref = tracks
        options = []
        for i, track in enumerate(tracks[:10]):
            label = f"{track.title[:90]}"
            description = f"{track.author[:50]}"
            options.append(discord.SelectOption(
                label=label, description=description, value=str(i), emoji="🎵"
            ))
        super().__init__(placeholder="🔎 Resultados encontrados...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        index = int(self.values[0])
        track = self.tracks_ref[index]
        track.requester = interaction.user # Salva quem pediu
        
        await self.player.queue.put_wait(track)
        if not self.player.playing:
            await self.player.play(self.player.queue.get())
            
        await interaction.response.send_message(f"✅ **{track.title}** adicionada à fila.", ephemeral=True)
        self.view.stop()
        try: await interaction.message.delete()
        except: pass

class TrackSelectView(discord.ui.View):
    def __init__(self, tracks: list[wavelink.Playable], player: wavelink.Player):
        super().__init__(timeout=60)
        self.add_item(TrackSelect(tracks, player))

class PlayerControlView(discord.ui.View):
    """Painel de Controle do Player."""
    def __init__(self, player: wavelink.Player):
        super().__init__(timeout=None)
        self.player = player

    async def update_message(self, interaction: discord.Interaction):
        embed = create_now_playing_embed(self.player)
        await interaction.response.edit_message(embed=embed, view=self)

    # --- LINHA 1: Controles de Reprodução ---
    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def restart(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.seek(0)
        await self.update_message(interaction)

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.pause(not self.player.paused)
        button.style = discord.ButtonStyle.danger if self.player.paused else discord.ButtonStyle.primary
        await self.update_message(interaction)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip(force=True)
        await interaction.response.send_message("⏭️ Pulado!", ephemeral=True)

    # Renomeado de 'stop' para 'stop_player' para evitar conflito com self.stop() da View
    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.disconnect()
        self.stop() # Agora chama o método da View corretamente
        await interaction.response.send_message("👋 Player fechado.", ephemeral=True)
        try: await interaction.message.delete()
        except: pass

    # --- LINHA 2: Volume e Fila ---
    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_vol = max(0, self.player.volume - 10)
        await self.player.set_volume(new_vol)
        await self.update_message(interaction)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        new_vol = min(100, self.player.volume + 10)
        await self.player.set_volume(new_vol)
        await self.update_message(interaction)

    @discord.ui.button(emoji="📜", label="Fila", style=discord.ButtonStyle.secondary, row=1)
    async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.queue.is_empty:
            return await interaction.response.send_message("📭 A fila está vazia.", ephemeral=True)
        
        queue_text = ""
        for i, track in enumerate(self.player.queue[:5]):
            queue_text += f"`{i+1}.` **{track.title}**\n"
        
        remaining = len(self.player.queue) - 5
        if remaining > 0: queue_text += f"\n*+ {remaining} outras...*"

        embed = discord.Embed(title="📜 Fila de Espera", description=queue_text, color=discord.Color.light_grey())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- LINHA 3: Modos e Atualização ---
    @discord.ui.button(emoji="🔁", label="Loop", style=discord.ButtonStyle.secondary, row=2)
    async def loop_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.queue.mode == wavelink.QueueMode.normal:
            self.player.queue.mode = wavelink.QueueMode.loop
            button.style = discord.ButtonStyle.success
            button.label = "1 Track"
        elif self.player.queue.mode == wavelink.QueueMode.loop:
            self.player.queue.mode = wavelink.QueueMode.loop_all
            button.style = discord.ButtonStyle.success
            button.label = "All Queue"
        else:
            self.player.queue.mode = wavelink.QueueMode.normal
            button.style = discord.ButtonStyle.secondary
            button.label = "Loop"
        await self.update_message(interaction)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=2)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.shuffle()
        await interaction.response.send_message("🔀 Embaralhado!", ephemeral=True)
        await self.update_message(interaction)

    @discord.ui.button(emoji="🔄", label="Sync", style=discord.ButtonStyle.primary, row=2)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_message(interaction)