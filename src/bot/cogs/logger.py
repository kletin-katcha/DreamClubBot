import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.guild_service import GuildService
import datetime

class Logger(commands.Cog):
    """
    Regista eventos do servidor (Mensagens, Membros, Voz) no canal de logs.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_log_channel(self, guild_id: int):
        """Busca o canal de logs configurado no banco."""
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(guild_id)
            if config and config.log_channel_id:
                return self.bot.get_channel(config.log_channel_id)
        return None

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or not before.guild:
            return
        
        # Ignora se o conteúdo não mudou (ex: o Discord apenas expandiu um link)
        if before.content == after.content:
            return

        channel = await self.get_log_channel(before.guild.id)
        if not channel: return

        embed = discord.Embed(title="✏️ Mensagem Editada", color=discord.Color.orange())
        embed.set_author(name=before.author.display_name, icon_url=before.author.display_avatar.url)
        embed.add_field(name="Canal", value=before.channel.mention, inline=False)
        # Limita o tamanho para não dar erro
        embed.add_field(name="Antes", value=before.content[:1024] or "*Sem conteúdo de texto*", inline=False)
        embed.add_field(name="Depois", value=after.content[:1024] or "*Sem conteúdo de texto*", inline=False)
        embed.set_footer(text=f"ID: {before.id}")
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        channel = await self.get_log_channel(message.guild.id)
        if not channel: return

        embed = discord.Embed(title="🗑️ Mensagem Apagada", color=discord.Color.red())
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Canal", value=message.channel.mention, inline=False)
        embed.add_field(name="Conteúdo", value=message.content[:1024] or "*Apenas anexo/embed*", inline=False)
        
        if message.attachments:
            embed.add_field(name="Anexos", value=f"{len(message.attachments)} arquivo(s)", inline=False)

        embed.set_footer(text=f"ID: {message.id}")
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild.id)
        if not channel: return

        # Calcula idade da conta
        now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
        created_at = member.created_at
        delta = now - created_at
        
        # Alerta se a conta for muito nova (menos de 24h)
        color = discord.Color.red() if delta.days < 1 else discord.Color.green()
        warning = "⚠️ **Conta Nova!** Cuidado." if delta.days < 1 else ""

        embed = discord.Embed(title="📥 Membro Entrou", description=f"{member.mention} {warning}", color=color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Conta Criada", value=f"<t:{int(created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = await self.get_log_channel(member.guild.id)
        if not channel: return

        embed = discord.Embed(title="📤 Membro Saiu", description=f"{member.mention} ({member.display_name})", color=discord.Color.dark_grey())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Cargos", value=f"{len(member.roles)-1}", inline=True)
        embed.timestamp = datetime.datetime.utcnow()

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        channel = await self.get_log_channel(member.guild.id)
        if not channel: return

        # Entrou em canal
        if not before.channel and after.channel:
            msg = f"🔊 Entrou em **{after.channel.name}**"
            color = discord.Color.green()
        # Saiu de canal
        elif before.channel and not after.channel:
            msg = f"🔇 Saiu de **{before.channel.name}**"
            color = discord.Color.red()
        # Mudou de canal
        elif before.channel and after.channel and before.channel.id != after.channel.id:
            msg = f"➡️ Moveu-se de **{before.channel.name}** para **{after.channel.name}**"
            color = discord.Color.blue()
        else:
            return # Outras mudanças (mute, deafen) ignoramos para não spammar

        embed = discord.Embed(description=f"**{member.display_name}**: {msg}", color=color)
        # Timestamp minimalista para logs de voz
        embed.set_footer(text=datetime.datetime.utcnow().strftime("%H:%M:%S"))
        
        await channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Logger(bot))