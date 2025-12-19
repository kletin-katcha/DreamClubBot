import os
import logging
import discord
import platform
import datetime
from discord.ext import commands
from bot.config import settings
from bot.core.database import init_db
import bot.models
from bot.utils.logger import TermColors

logger = logging.getLogger("BotClient")

class DreamClubBot(commands.Bot):
    """
    Classe principal do Dream Club Bot com suporte a Perfis (Main/Music).
    """

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix=settings.command_prefix,
            intents=intents,
            help_command=None,
            activity=discord.Game(name=f"Iniciando {settings.bot_profile}...")
        )

    async def setup_hook(self) -> None:
        """Configuração inicial ao ligar."""
        logger.info(f"--- Setup Hook ({settings.bot_profile}) ---")
        
        # 1. Banco de Dados
        # Apenas o MAIN deve criar tabelas para evitar conflitos de escrita (Database Locked)
        if settings.bot_profile == "MAIN":
            logger.info("Verificando integridade do Banco de Dados...")
            await init_db()
        
        # 2. Carregar Cogs (Baseado no Perfil)
        await self.load_cogs()
        
        # 3. Sincronizar Comandos
        try:
            # Sincroniza os comandos Slash com o Discord
            # Isso é crucial para o /play e outros comandos aparecerem
            synced = await self.tree.sync()
            logger.info(f"Comandos Slash Sincronizados: {len(synced)}")
        except Exception as e:
            logger.error(f"Erro no Sync: {e}")

    async def load_cogs(self):
        """
        Carrega os módulos dinamicamente baseado no PERFIL do bot.
        """
        cogs_path = os.path.join(os.path.dirname(__file__), 'cogs')
        count = 0
        
        if not os.path.exists(cogs_path):
            logger.warning("Pasta 'cogs' não encontrada!")
            return

        # Definição dos Perfis
        # MAIN: Carrega tudo.
        # MUSIC: Carrega apenas música e gestão básica.
        
        is_music_bot = "MUSIC" in settings.bot_profile
        
        # Lista de Cogs permitidos para bots de música
        MUSIC_WHITELIST = ["music", "manager"] 

        for filename in os.listdir(cogs_path):
            name = None
            
            # Deteta arquivo .py
            if filename.endswith('.py') and not filename.startswith('__'):
                name = filename[:-3]
            # Deteta pasta (pacote) com __init__.py
            elif os.path.isdir(os.path.join(cogs_path, filename)):
                if os.path.exists(os.path.join(cogs_path, filename, '__init__.py')):
                    name = filename

            if name:
                # --- FILTRAGEM INTELIGENTE ---
                if is_music_bot:
                    # Se for bot de música, só carrega o que está na whitelist
                    if name not in MUSIC_WHITELIST:
                        continue
                
                # Se for MAIN, carrega tudo (não fazemos continue)
                
                # Tenta carregar
                try:
                    await self.load_extension(f'bot.cogs.{name}')
                    logger.info(f"Módulo carregado: {TermColors.GREEN}{name}{TermColors.RESET}")
                    count += 1
                except Exception as e:
                    logger.error(f"Falha ao carregar {name}: {e}")
        
        logger.info(f"Total de módulos ativos para {settings.bot_profile}: {count}")

    async def on_ready(self):
        # Define o status baseado no perfil
        status_text = "Dream Club Members"
        if "MUSIC" in settings.bot_profile:
            status_text = "Música de Alta Qualidade"

        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=status_text))
        
        print(f"\n{TermColors.CYAN}")
        print(r"""
  ____  ____  _____    _    __  __     ____ _     _   _ ____  
 |  _ \|  _ \| ____|  / \  |  \/  |   / ___| |   | | | | __ ) 
 | | | | |_) |  _|   / _ \ | |\/| |  | |   | |   | | | |  _ \ 
 | |_| |  _ <| |___ / ___ \| |  | |  | |___| |___| |_| | |_) |
 |____/|_| \_\_____/_/   \_\_|  |_|   \____|_____|\___/|____/ 
        """)
        print(f"{TermColors.RESET}")
        
        print(f"{TermColors.BOLD}╔══════════════════ SISTEMA ONLINE ══════════════════╗{TermColors.RESET}")
        print(f"║ 🤖 {TermColors.BOLD}Bot:{TermColors.RESET}       {self.user.name}#{self.user.discriminator}")
        print(f"║ 🆔 {TermColors.BOLD}ID:{TermColors.RESET}        {self.user.id}")
        print(f"║ 👤 {TermColors.BOLD}Perfil:{TermColors.RESET}    {settings.bot_profile}")
        print(f"║ 📡 {TermColors.BOLD}Latency:{TermColors.RESET}   {round(self.latency * 1000)}ms")
        print(f"║ 🕒 {TermColors.BOLD}Time:{TermColors.RESET}      {datetime.datetime.now().strftime('%H:%M:%S')}")
        print(f"{TermColors.BOLD}╚════════════════════════════════════════════════════╝{TermColors.RESET}\n")
        
        logger.info("A aguardar eventos...")