import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.tag_service import TagService

class Tags(commands.Cog):
    """
    Sistema de respostas rápidas e conhecimento.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete para facilitar a vida ---
    async def tag_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        async with get_session() as session:
            service = TagService(session)
            tags = await service.list_tags(interaction.guild.id)
            
            # Filtra as tags que começam com o que o usuário digitou
            return [
                app_commands.Choice(name=t.name, value=t.name)
                for t in tags if current.lower() in t.name.lower()
            ][:25] # Limite do Discord

    @app_commands.command(name="tag", description="Mostra o conteúdo de uma tag.")
    @app_commands.autocomplete(nome=tag_autocomplete)
    async def tag_show(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = TagService(session)
            tag = await service.get_tag(interaction.guild.id, nome)
            
        if tag:
            # Resposta simples e direta
            await interaction.followup.send(tag.content)
        else:
            await interaction.followup.send(f"❌ Tag `{nome}` não encontrada.", ephemeral=True)

    @app_commands.command(name="tag_criar", description="[Admin] Cria uma nova resposta rápida.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def tag_create(self, interaction: discord.Interaction, nome: str, conteudo: str):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = TagService(session)
            tag, msg = await service.create_tag(interaction.guild.id, interaction.user.id, nome, conteudo)
            
        if tag:
            await interaction.followup.send(f"✅ Tag **{tag.name}** criada com sucesso!")
        else:
            await interaction.followup.send(f"❌ Erro: {msg}")

    @app_commands.command(name="tag_deletar", description="[Admin] Remove uma tag existente.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.autocomplete(nome=tag_autocomplete)
    async def tag_delete(self, interaction: discord.Interaction, nome: str):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = TagService(session)
            success = await service.delete_tag(interaction.guild.id, nome)
            
        if success:
            await interaction.followup.send(f"🗑️ Tag **{nome}** removida.")
        else:
            await interaction.followup.send(f"❌ Tag `{nome}` não encontrada.")

    @app_commands.command(name="tag_lista", description="Vê todas as tags disponíveis.")
    async def tag_list(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = TagService(session)
            tags = await service.list_tags(interaction.guild.id)
            
        if not tags:
            await interaction.followup.send("📭 Nenhuma tag criada neste servidor.")
            return

        # Formata a lista
        tag_names = [f"`{t.name}`" for t in tags]
        description = ", ".join(tag_names)
        
        embed = discord.Embed(
            title=f"📚 Tags do Servidor ({len(tags)})",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use /tag [nome] para ver o conteúdo.")
        
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tags(bot))