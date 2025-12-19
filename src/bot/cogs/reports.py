import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.report_service import ReportService
from bot.services.guild_service import GuildService

class ReportView(discord.ui.View):
    def __init__(self, target_id: int):
        super().__init__(timeout=None)
        self.target_id = target_id

    @discord.ui.button(label="Banir", style=discord.ButtonStyle.danger, emoji="🔨")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            guild = interaction.guild
            member = guild.get_member(self.target_id) or await guild.fetch_member(self.target_id)
            await member.ban(reason="Banido via Painel de Denúncias")
            await interaction.followup.send(f"✅ **{member}** foi banido com sucesso.")
            self.stop()
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao banir: {e}")

    @discord.ui.button(label="Expulsar", style=discord.ButtonStyle.secondary, emoji="👢")
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            guild = interaction.guild
            member = guild.get_member(self.target_id) or await guild.fetch_member(self.target_id)
            await member.kick(reason="Expulso via Painel de Denúncias")
            await interaction.followup.send(f"✅ **{member}** foi expulso.")
            self.stop()
        except Exception as e:
            await interaction.followup.send(f"❌ Erro ao expulsar: {e}")

    @discord.ui.button(label="Descartar", style=discord.ButtonStyle.success, emoji="✅")
    async def dismiss_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.edit(content="~~Denúncia Resolvida/Descartada~~", view=None)
        await interaction.response.send_message("Denúncia arquivada.", ephemeral=True)
        self.stop()

class Reports(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Context Menu: Reportar Mensagem (Clique Direito)
        self.ctx_menu = app_commands.ContextMenu(
            name="🚩 Reportar Mensagem",
            callback=self.report_message_ctx
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def send_report_log(self, guild, report_data):
        async with get_session() as session:
            g_service = GuildService(session)
            config = await g_service.get_config(guild.id)
            
            # Tenta usar o campo report_channel_id (adicionado recentemente)
            # Se der erro de atributo (caso não tenha reiniciado o banco), usa log_channel_id como fallback
            channel_id = getattr(config, "report_channel_id", None) or config.log_channel_id
            
            if not channel_id:
                return False

            channel = guild.get_channel(channel_id)
            if not channel:
                return False

            embed = discord.Embed(title="🚨 Nova Denúncia", color=discord.Color.red())
            embed.add_field(name="Acusado", value=f"<@{report_data['target_id']}> (`{report_data['target_id']}`)", inline=True)
            embed.add_field(name="Denunciante", value=f"<@{report_data['reporter_id']}>", inline=True)
            embed.add_field(name="Motivo", value=report_data['reason'], inline=False)
            
            if report_data.get('content'):
                embed.add_field(name="Conteúdo da Mensagem", value=report_data['content'][:1000], inline=False)
            
            if report_data.get('proof'):
                embed.set_image(url=report_data['proof'])

            embed.timestamp = datetime.datetime.utcnow()
            
            await channel.send(embed=embed, view=ReportView(report_data['target_id']))
            return True

    @app_commands.command(name="reportar", description="Denuncia um usuário para a staff.")
    @app_commands.describe(usuario="Quem você quer denunciar", motivo="O que ele fez?", prova="Link ou anexo (Opcional)")
    async def reportar(self, interaction: discord.Interaction, usuario: discord.Member, motivo: str, prova: discord.Attachment = None):
        if usuario.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode se denunciar.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        proof_url = prova.url if prova else None

        async with get_session() as session:
            service = ReportService(session)
            await service.create_report(
                interaction.guild.id,
                interaction.user.id,
                usuario.id,
                motivo,
                proof=proof_url
            )

        # Envia para o canal da staff
        sent = await self.send_report_log(interaction.guild, {
            'target_id': usuario.id,
            'reporter_id': interaction.user.id,
            'reason': motivo,
            'proof': proof_url
        })

        if sent:
            await interaction.followup.send("✅ Denúncia enviada com sucesso! A Staff irá analisar.")
        else:
            await interaction.followup.send("⚠️ Denúncia registada, mas o canal de reports não está configurado.")

    async def report_message_ctx(self, interaction: discord.Interaction, message: discord.Message):
        if message.author.id == interaction.user.id:
            await interaction.response.send_message("❌ Não pode denunciar a própria mensagem.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = ReportService(session)
            await service.create_report(
                interaction.guild.id,
                interaction.user.id,
                message.author.id,
                "Via Menu de Contexto (Mensagem Inapropriada)",
                content=message.content
            )

        sent = await self.send_report_log(interaction.guild, {
            'target_id': message.author.id,
            'reporter_id': interaction.user.id,
            'reason': "Mensagem Reportada (Clique Direito)",
            'content': message.content,
            'proof': None
        })

        await interaction.followup.send("✅ Mensagem reportada à administração.")

    @app_commands.command(name="config_reports", description="[Admin] Define o canal de denúncias.")
    @app_commands.checks.has_permissions(administrator=True)
    async def config_reports(self, interaction: discord.Interaction, canal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            # Assumindo que GuildConfig já foi atualizado com o campo
            g_service = GuildService(session)
            config = await g_service.get_config(interaction.guild.id)
            
            # Atualização manual do campo se o método específico não existir no service
            config.report_channel_id = canal.id
            session.add(config)
            await session.commit()
            
        await interaction.followup.send(f"✅ Canal de denúncias definido para: {canal.mention}")

import datetime
async def setup(bot: commands.Bot):
    await bot.add_cog(Reports(bot))