import logging
import discord
from discord.ext import commands
import traceback
import sys

# Configuração de log local para este módulo
logger = logging.getLogger(__name__)

class Manager(commands.Cog):
    """
    Cog responsável por eventos globais e tratamento de erros.
    Atua como um gerenciador administrativo do bot.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Evento disparado quando o Cog é carregado e o bot está pronto.
        Define o status/atividade do bot.
        """
        # Define a atividade "Assistindo Homens evoluindo"
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name='Homens evoluindo'
        )
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
        logger.info(f"Manager Cog carregado: Status definido para '{activity.name}'.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """
        Tratador global de erros para comandos de texto (prefix commands).
        Intercepta falhas e responde apropriadamente ao usuário.
        """
        
        # Se o comando tiver seu próprio tratamento de erro local, ignoramos aqui.
        if hasattr(ctx.command, 'on_error'):
            return

        # Recupera o erro original se ele foi encapsulado (comum em discord.py)
        error = getattr(error, 'original', error)

        # 1. Comando não encontrado
        if isinstance(error, commands.CommandNotFound):
            # Ignoramos silenciosamente para não poluir o log com typos de usuários
            return

        # 2. Usuário sem permissão
        elif isinstance(error, commands.MissingPermissions):
            missing = ", ".join(error.missing_permissions)
            await ctx.send(f"🚫 **Acesso Negado:** Você precisa das permissões `{missing}` para usar este comando.")
            logger.warning(f"Usuário {ctx.author} tentou usar '{ctx.command}' sem permissão.")

        # 3. Bot sem permissão
        elif isinstance(error, commands.BotMissingPermissions):
            missing = ", ".join(error.missing_permissions)
            await ctx.send(f"⚠️ **Erro de Permissão:** Eu preciso das permissões `{missing}` para executar isso.")
        
        # 4. Comando usado em DM mas é exclusivo de servidor
        elif isinstance(error, commands.NoPrivateMessage):
            try:
                await ctx.author.send("❌ Este comando não pode ser usado em mensagens diretas (DM).")
            except discord.Forbidden:
                pass # Se não conseguirmos enviar DM, apenas ignoramos

        # 5. Erros de Argumentos (Faltando ou inválidos)
        elif isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument)):
            await ctx.send(
                f"📝 **Uso incorreto:** {error}\n"
                f"Tente usar `{ctx.prefix}help {ctx.command}` para ver como usar."
            )

        # 6. Erro Genérico/Desconhecido
        else:
            # Envia mensagem amigável ao usuário
            await ctx.send("💥 **Ocorreu um erro inesperado.** O administrador foi notificado.")
            
            # Loga o erro completo no console/arquivo para debug
            logger.error(f"Erro não tratado no comando '{ctx.command}':", exc_info=error)
            
            # Opcional: Imprimir traceback no stderr (padrão do Python)
            # print(f'Ignorando exceção no comando {ctx.command}:', file=sys.stderr)
            # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

async def setup(bot: commands.Bot):
    """Função de setup obrigatória para carregar a extensão."""
    await bot.add_cog(Manager(bot))