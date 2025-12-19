import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.library_service import LibraryService
from bot.services.user_service import UserService

class Library(commands.Cog):
    """
    Biblioteca comunitária de conhecimento.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    CATEGORIAS = [
        app_commands.Choice(name="Livros", value="Livros"),
        app_commands.Choice(name="Vídeos", value="Vídeos"),
        app_commands.Choice(name="Podcasts", value="Podcasts"),
        app_commands.Choice(name="Artigos", value="Artigos"),
        app_commands.Choice(name="Filmes", value="Filmes"),
    ]

    @app_commands.command(name="sugerir", description="Sugira um material de estudo para a biblioteca.")
    @app_commands.choices(categoria=CATEGORIAS)
    async def sugerir(self, interaction: discord.Interaction, titulo: str, link: str, categoria: app_commands.Choice[str]):
        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = LibraryService(session)
            resource = await service.suggest_resource(
                interaction.user.id, 
                titulo, 
                link, 
                categoria.value
            )

        await interaction.followup.send(
            f"✅ **Sugestão enviada!**\nID: `{resource.id}` - *{resource.title}*\n"
            "Aguarde a aprovação da moderação. Se aprovado, ganhará XP!"
        )

    @app_commands.command(name="biblioteca", description="Consulte os materiais aprovados.")
    @app_commands.choices(categoria=CATEGORIAS)
    async def biblioteca(self, interaction: discord.Interaction, categoria: app_commands.Choice[str] = None):
        await interaction.response.defer()
        
        cat_filter = categoria.value if categoria else None
        
        async with get_session() as session:
            service = LibraryService(session)
            resources = await service.list_approved(cat_filter)

        if not resources:
            msg = f"📚 Nenhum material encontrado na categoria **{cat_filter}**." if cat_filter else "📚 A biblioteca está vazia no momento."
            await interaction.followup.send(msg)
            return

        embed = discord.Embed(
            title=f"📚 Biblioteca: {cat_filter if cat_filter else 'Geral'}",
            color=discord.Color.blue()
        )
        
        for res in resources[:10]:
            submitter = interaction.guild.get_member(res.submitter_id)
            name = submitter.display_name if submitter else "Membro Desconhecido"
            
            embed.add_field(
                name=f"📖 {res.title} ({res.category})",
                value=f"🔗 [Acessar Link]({res.link})\n👤 Sugerido por: {name}",
                inline=False
            )
            
        embed.set_footer(text="Use /sugerir para contribuir com a comunidade.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="recursos_pendentes", description="[Admin] Lista sugestões aguardando aprovação.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def recursos_pendentes(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = LibraryService(session)
            pending = await service.list_pending()
            
        if not pending:
            await interaction.followup.send("✅ Não há sugestões pendentes.")
            return
            
        msg = "**📋 Fila de Aprovação:**\n"
        for p in pending:
            msg += f"`ID: {p.id}` | **{p.title}** ({p.category}) | [Link]({p.link}) | User: <@{p.submitter_id}>\n"
            
        await interaction.followup.send(msg)

    @app_commands.command(name="recurso_aprovar", description="[Admin] Aprova um recurso e dá XP ao autor.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def recurso_aprovar(self, interaction: discord.Interaction, id_recurso: int):
        await interaction.response.defer()
        
        async with get_session() as session:
            lib_service = LibraryService(session)
            user_service = UserService(session)
            
            resource = await lib_service.approve_resource(id_recurso)
            
            if not resource:
                await interaction.followup.send("❌ Recurso não encontrado.")
                return
                
            xp_reward = 150
            leveled_up = await user_service.add_xp(resource.submitter_id, xp_reward)
            
            await interaction.followup.send(f"✅ **Aprovado!** O recurso **{resource.title}** foi adicionado à biblioteca.")
            
            try:
                author = interaction.guild.get_member(resource.submitter_id)
                if author:
                    msg = f"📚 Sua sugestão **{resource.title}** foi aprovada!\n💎 Ganhaste **{xp_reward} XP**."
                    if leveled_up: 
                        msg += "\n🏆 **LEVEL UP!**"
                    await author.send(msg)
            except:
                pass

    @app_commands.command(name="recurso_rejeitar", description="[Admin] Rejeita e apaga uma sugestão.")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def recurso_rejeitar(self, interaction: discord.Interaction, id_recurso: int):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = LibraryService(session)
            success = await service.delete_resource(id_recurso)
            
        if success:
            await interaction.followup.send(f"🗑️ Recurso {id_recurso} rejeitado e removido.")
        else:
            await interaction.followup.send("❌ Recurso não encontrado.")

# A FUNÇÃO ABAIXO É OBRIGATÓRIA
async def setup(bot: commands.Bot):
    await bot.add_cog(Library(bot))