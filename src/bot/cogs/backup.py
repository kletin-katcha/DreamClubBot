import discord
from discord import app_commands
from discord.ext import commands, tasks
import shutil
import os
import datetime
import logging

logger = logging.getLogger(__name__)

class BackupSystem(commands.Cog):
    """
    Sistema de segurança de dados.
    Realiza cópias do banco de dados periodicamente.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.backup_loop.start()
        
        # Garante que a pasta existe
        if not os.path.exists("backups"):
            os.makedirs("backups")

    def cog_unload(self):
        self.backup_loop.cancel()

    def create_backup(self) -> str:
        """Cria um arquivo de backup e retorna o caminho."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        source = "bot.db"
        destination = f"backups/backup_{timestamp}.db"
        
        if not os.path.exists(source):
            return None

        shutil.copy2(source, destination)
        return destination

    def cleanup_old_backups(self, max_files: int = 10):
        """Mantém apenas os X backups mais recentes."""
        folder = "backups"
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".db")]
        
        # Ordena por data de criação (mais antigo primeiro)
        files.sort(key=os.path.getctime)
        
        # Se tiver mais que o limite, apaga os antigos
        if len(files) > max_files:
            for f in files[:-max_files]:
                try:
                    os.remove(f)
                    logger.info(f"Backup antigo removido: {f}")
                except Exception as e:
                    logger.error(f"Erro ao limpar backup {f}: {e}")

    @tasks.loop(hours=6)
    async def backup_loop(self):
        """Tarefa automática a cada 6 horas."""
        try:
            filename = await self.bot.loop.run_in_executor(None, self.create_backup)
            if filename:
                logger.info(f"✅ Backup automático criado: {filename}")
                # Limpa antigos
                await self.bot.loop.run_in_executor(None, self.cleanup_old_backups, 20)
        except Exception as e:
            logger.error(f"Falha no backup automático: {e}")

    @app_commands.command(name="backup_criar", description="[Admin] Força a criação de um backup agora.")
    @app_commands.checks.has_permissions(administrator=True)
    async def force_backup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            filename = await self.bot.loop.run_in_executor(None, self.create_backup)
            if filename:
                size_bytes = os.path.getsize(filename)
                size_mb = size_bytes / (1024 * 1024)
                await interaction.followup.send(f"✅ **Backup Criado!**\nArquivo: `{filename}`\nTamanho: `{size_mb:.2f} MB`")
            else:
                await interaction.followup.send("❌ Erro: O arquivo `bot.db` não foi encontrado na raiz.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro interno: {e}")

    @app_commands.command(name="backup_download", description="[Admin] Recebe o último backup na DM.")
    @app_commands.checks.has_permissions(administrator=True)
    async def download_backup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True) # Privado por segurança!
        
        folder = "backups"
        if not os.path.exists(folder) or not os.listdir(folder):
            # Tenta criar um agora
            self.create_backup()
        
        # Pega o mais recente
        files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".db")]
        if not files:
            await interaction.followup.send("❌ Nenhum backup disponível.")
            return
            
        latest_file = max(files, key=os.path.getctime)
        
        try:
            file = discord.File(latest_file)
            await interaction.user.send("🔒 **Backup solicitado via Painel Admin.**\nGuarde este arquivo em segurança.", file=file)
            await interaction.followup.send("✅ Enviei o arquivo para a sua DM (Direct Message).")
        except discord.Forbidden:
            await interaction.followup.send("❌ Não consegui enviar DM. Verifique as suas configurações de privacidade.")
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao enviar: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(BackupSystem(bot))