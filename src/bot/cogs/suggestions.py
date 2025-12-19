import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.suggestion_service import SuggestionService
from bot.services.guild_service import GuildService
from bot.services.user_service import UserService
from bot.utils.embeds import EmbedFactory, DreamColors

class Suggestions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sugestao", description="Envia uma ideia para melhorar o servidor.")
    async def sugerir(self, interaction: discord.Interaction, ideia: str):
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            guild_service = GuildService(session)
            config = await guild_service.get_config(interaction.guild.id)
            channel_id = getattr(config, "suggestion_channel_id", None) 

            if not channel_id:
                await interaction.followup.send(embed=EmbedFactory.error("Canal de sugestões não configurado."))
                return

            channel = interaction.guild.get_channel(channel_id)
            if not channel:
                await interaction.followup.send(embed=EmbedFactory.error("Canal de sugestões não encontrado."))
                return

            # Embed da Sugestão
            embed = EmbedFactory.create(
                description=ideia,
                color=DreamColors.WARNING, # Amarelo = Pendente
                author=interaction.user,
                footer="Vote com as reações abaixo!"
            )
            
            msg = await channel.send(embed=embed)
            await msg.add_reaction("👍")
            await msg.add_reaction("👎")

            service = SuggestionService(session)
            suggestion = await service.create_suggestion(
                interaction.guild.id,
                interaction.user.id,
                msg.id,
                ideia
            )
            
            # Atualiza ID no rodapé
            embed.set_footer(text=f"ID: {suggestion.id} | Vote com as reações abaixo!")
            await msg.edit(embed=embed)

        await interaction.followup.send(embed=EmbedFactory.success(f"Sugestão enviada para {channel.mention}!"))

    @app_commands.command(name="sugestao_analisar", description="[Admin] Aprova ou rejeita uma sugestão.")
    @app_commands.choices(acao=[
        app_commands.Choice(name="Aprovar", value="approved"),
        app_commands.Choice(name="Rejeitar", value="rejected")
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def sugestao_analisar(self, interaction: discord.Interaction, id_sugestao: int, acao: app_commands.Choice[str], motivo: str = None):
        await interaction.response.defer()

        async with get_session() as session:
            suggestion_service = SuggestionService(session)
            sug = await suggestion_service.get_suggestion(id_sugestao)

            if not sug:
                await interaction.followup.send(embed=EmbedFactory.error("Sugestão não encontrada."))
                return

            guild_service = GuildService(session)
            config = await guild_service.get_config(interaction.guild.id)
            channel = interaction.guild.get_channel(config.suggestion_channel_id)
            
            try:
                msg = await channel.fetch_message(sug.message_id)
            except:
                await interaction.followup.send(embed=EmbedFactory.error("Mensagem original apagada."))
                return

            new_status = acao.value
            await suggestion_service.update_status(sug.id, new_status)

            embed = msg.embeds[0]
            if new_status == "approved":
                embed.color = DreamColors.SUCCESS
                embed.title = "✅ Sugestão Aprovada"
                user_service = UserService(session)
                await user_service.add_xp(sug.author_id, 100)
            else:
                embed.color = DreamColors.ERROR
                embed.title = "❌ Sugestão Rejeitada"

            if motivo:
                # Remove campos antigos para não duplicar se editar de novo
                embed.clear_fields()
                embed.add_field(name="Motivo da Decisão", value=motivo, inline=False)
            
            embed.set_footer(text=f"ID: {sug.id} | Analisado por {interaction.user.display_name}")
            await msg.edit(embed=embed)
            
            try:
                author = interaction.guild.get_member(sug.author_id)
                if author:
                    status_pt = "Aprovada" if new_status == "approved" else "Rejeitada"
                    # Embed na DM
                    dm_embed = EmbedFactory.create(
                        title=f"Sugestão {status_pt}",
                        description=f"Sua sugestão **#{sug.id}** foi processada.",
                        color=embed.color
                    )
                    if motivo: dm_embed.add_field(name="Motivo", value=motivo)
                    await author.send(embed=dm_embed)
            except: pass

        await interaction.followup.send(embed=EmbedFactory.success(f"Sugestão #{sug.id} atualizada."))

    @app_commands.command(name="config_sugestoes", description="[Admin] Define o canal de sugestões.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_sugestoes(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = GuildService(session)
            config = await service.get_config(interaction.guild.id)
            config.suggestion_channel_id = canal.id
            session.add(config)
            await session.commit()
            
        await interaction.followup.send(embed=EmbedFactory.success(f"Canal definido para: {canal.mention}"))

async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))