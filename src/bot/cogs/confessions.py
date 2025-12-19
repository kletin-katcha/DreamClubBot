import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.confession_service import ConfessionService
from bot.services.guild_service import GuildService

class Confessions(commands.Cog):
    """
    Sistema de mensagens anónimas para apoio comunitário.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="confessar", description="Envia um desabafo anónimo para o canal oficial.")
    @app_commands.describe(texto="O que te vai na alma?")
    async def confessar(self, interaction: discord.Interaction, texto: str):
        # Resposta efêmera para ninguém ver que foste tu a digitar
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            # 1. Busca Configuração
            guild_service = GuildService(session)
            config = await guild_service.get_config(interaction.guild.id)
            
            # Tenta pegar o ID do canal (lida com o caso de o campo ainda não existir na classe Python se não tiver reiniciado)
            channel_id = getattr(config, "confession_channel_id", None)

            if not channel_id:
                await interaction.followup.send("❌ O canal de desabafos não está configurado.")
                return

            channel = interaction.guild.get_channel(channel_id)
            if not channel:
                await interaction.followup.send("❌ Canal de desabafos não encontrado.")
                return

            # 2. Envia Embed Anónimo
            # Usamos uma cor aleatória ou fixa para estética
            embed = discord.Embed(
                description=texto,
                color=discord.Color.from_rgb(47, 49, 54) # Cor escura "Dark Mode"
            )
            embed.set_author(name="Desabafo Anónimo", icon_url="https://i.imgur.com/7P5lU2W.png") # Ícone de máscara ou fantasma
            embed.set_footer(text="Se precisares de ajuda profissional, procura um médico.")
            
            msg = await channel.send(embed=embed)

            # 3. Salva no Banco (Para a staff saber quem foi em caso de crime/abuso)
            service = ConfessionService(session)
            confession = await service.create_confession(
                interaction.guild.id,
                interaction.user.id,
                msg.id,
                texto
            )
            
            # Atualiza o footer com o ID do desabafo
            embed.set_footer(text=f"Desabafo #{confession.id} | Enviado via /confessar")
            await msg.edit(embed=embed)

        await interaction.followup.send(f"✅ O teu desabafo foi enviado de forma anónima para {channel.mention}.")

    @app_commands.command(name="config_desabafos", description="[Admin] Define o canal de confissões.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_desabafos(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            g_service = GuildService(session)
            config = await g_service.get_config(interaction.guild.id)
            
            config.confession_channel_id = canal.id
            session.add(config)
            await session.commit()
            
        await interaction.followup.send(f"✅ Canal de desabafos definido para: {canal.mention}")

    @app_commands.command(name="confissao_investigar", description="[Admin] Revela o autor de um desabafo (Apenas emergências).")
    @app_commands.checks.has_permissions(administrator=True)
    async def investigar(self, interaction: discord.Interaction, id_desabafo: int):
        await interaction.response.defer(ephemeral=True) # Resposta privada!
        
        async with get_session() as session:
            service = ConfessionService(session)
            confession = await service.get_confession(id_desabafo)
            
            if not confession:
                await interaction.followup.send("❌ Desabafo não encontrado.")
                return
                
            author = interaction.guild.get_member(confession.author_id)
            author_text = f"{author.mention} ({author.id})" if author else f"ID: {confession.author_id} (Saiu do servidor)"
            
            await interaction.followup.send(
                f"🕵️ **Relatório de Investigação**\n"
                f"**Desabafo:** #{confession.id}\n"
                f"**Autor:** {author_text}\n"
                f"**Data:** <t:{int(confession.created_at.timestamp())}:F>\n"
                f"**Conteúdo:**\n{confession.content}"
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Confessions(bot))