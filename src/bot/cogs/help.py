import discord
from discord import app_commands
from discord.ext import commands

class HelpSelect(discord.ui.Select):
    """Menu dinâmico que lista todos os Cogs (módulos) carregados."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = []
        
        # Mapeamento de Emojis
        self.emoji_map = {
            "Profile": "👤", "Music": "🎵", "MusicCog": "🎵", "Moderation": "🛡️",
            "Daily": "☀️", "Goals": "🎯", "Habits": "📅", "Journal": "📔",
            "Shop": "🛒", "Tribes": "🏰", "Mentorship": "🤝", "Challenges": "🔥",
            "Library": "📚", "Focus": "🧘", "Quiz": "🧠", "Tickets": "📩",
            "Reminders": "⏰", "Welcome": "👋", "VoiceMaster": "🔊",
            "Giveaways": "🎉", "ReactionRoles": "🎭", "AutoMod": "🤖",
            "Manager": "⚙️", "Ranking": "🏆"
        }

        # Opção Inicial (Home)
        options.append(discord.SelectOption(
            label="Início", 
            value="home", 
            emoji="🏠", 
            description="Voltar ao menu principal"
        ))

        # Loop Mágico: Itera sobre todos os Cogs carregados no Bot
        for cog_name, cog in sorted(bot.cogs.items()):
            slash_commands = cog.get_app_commands()
            text_commands = cog.get_commands()
            
            if not slash_commands and not text_commands:
                continue
                
            if cog_name == "CustomHelp":
                continue

            emoji = self.emoji_map.get(cog_name, "🔧")
            description = cog.description[:100] if cog.description else "Comandos diversos"
            
            options.append(discord.SelectOption(
                label=cog_name,
                value=cog_name,
                emoji=emoji,
                description=description
            ))

        super().__init__(placeholder="📖 Escolha uma categoria...", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        val = self.values[0]
        
        # Se escolheu Início, volta ao embed original
        if val == "home":
            await interaction.response.edit_message(embed=self.view.home_embed, view=self.view)
            return

        # Busca o Cog selecionado
        cog = self.bot.get_cog(val)
        if not cog:
            await interaction.response.edit_message(content="❌ Erro: Categoria não encontrada.", view=self.view)
            return

        embed = discord.Embed(
            title=f"{self.emoji_map.get(val, '🔧')} {val}",
            description=cog.description or "Sem descrição disponível.",
            color=discord.Color.blue()
        )
        
        # Função auxiliar para garantir que não estouramos o limite de 1024 caracteres
        def truncate_text(lines, limit=1000):
            text = ""
            for line in lines:
                if len(text) + len(line) > limit:
                    text += "... (lista truncada)"
                    break
                text += line
            return text

        # Lista Comandos Slash
        app_cmds = cog.get_app_commands()
        if app_cmds:
            lines = [f"`/{cmd.name}` - {cmd.description}\n" for cmd in app_cmds]
            final_text = truncate_text(lines)
            if final_text:
                embed.add_field(name="Comandos Slash", value=final_text, inline=False)

        # Lista Comandos de Texto
        txt_cmds = cog.get_commands()
        if txt_cmds:
            lines = []
            for cmd in txt_cmds:
                desc = cmd.help if cmd.help else "Sem descrição"
                lines.append(f"`!{cmd.name}` - {desc}\n")
            
            final_text = truncate_text(lines)
            if final_text:
                embed.add_field(name="Comandos de Texto", value=final_text, inline=False)

        await interaction.response.edit_message(embed=embed, view=self.view)

class HelpView(discord.ui.View):
    def __init__(self, bot: commands.Bot, home_embed: discord.Embed):
        super().__init__(timeout=120)
        self.home_embed = home_embed
        self.add_item(HelpSelect(bot))

class CustomHelp(commands.Cog):
    """
    Sistema de Ajuda Dinâmico.
    Lê automaticamente todos os comandos do bot.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="ajuda", description="Mostra todos os comandos disponíveis.")
    async def ajuda(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📘 Manual do Dream Club Bot",
            description=(
                "Bem-vindo ao sistema de ajuda dinâmica.\n"
                "Selecione uma categoria abaixo para ver os comandos disponíveis.\n\n"
                "ℹ️ **Este menu é atualizado automaticamente.**\n"
                "Sempre que novos recursos forem adicionados, aparecerão aqui."
            ),
            color=discord.Color.blue()
        )
        if self.bot.user.display_avatar:
             embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Total de módulos carregados: {len(self.bot.cogs)}")
        
        view = HelpView(self.bot, embed)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomHelp(bot))