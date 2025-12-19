import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.tribe_service import TribeService

class Tribes(commands.Cog):
    """
    Sistema de Tribos e Alianças.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="tribo_criar", description="Funda uma nova tribo (Custo: 1000 XP).")
    @app_commands.describe(nome="Nome da tua Tribo", lema="Descrição ou lema curto")
    async def tribo_criar(self, interaction: discord.Interaction, nome: str, lema: str):
        await interaction.response.defer()

        async with get_session() as session:
            service = TribeService(session)
            success, msg, tribe = await service.create_tribe(interaction.user.id, nome, lema)

        if success:
            await interaction.followup.send(f"🏰 **Tribo Fundada!**\nParabéns, líder! A tribo **{tribe.name}** nasceu.\nLema: *{tribe.description}*")
        else:
            await interaction.followup.send(f"❌ {msg}")

    @app_commands.command(name="tribo", description="Vê o perfil da tua tribo ou de outro membro.")
    async def tribo_perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        await interaction.response.defer()

        async with get_session() as session:
            service = TribeService(session)
            tribe, member_record = await service.get_user_tribe(target.id)
            
            if not tribe:
                msg = f"{target.display_name} é um lobo solitário (sem tribo)." if membro else "Você não tem tribo. Use `/tribo_criar` ou peça um convite."
                await interaction.followup.send(msg)
                return

            member_count = await service.get_members_count(tribe.id)
            leader = interaction.guild.get_member(tribe.leader_id)
            leader_name = leader.display_name if leader else "Desconhecido"

            embed = discord.Embed(title=f"🛡️ Tribo: {tribe.name}", description=f"*{tribe.description}*", color=discord.Color.dark_red())
            embed.add_field(name="Líder", value=leader_name, inline=True)
            embed.add_field(name="Membros", value=str(member_count), inline=True)
            embed.add_field(name="Fundada em", value=tribe.created_at.strftime("%d/%m/%Y"), inline=False)
            
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="tribo_convidar", description="Convida alguém para a tua tribo.")
    async def tribo_convidar(self, interaction: discord.Interaction, membro: discord.Member):
        if membro.id == interaction.user.id or membro.bot:
            await interaction.response.send_message("❌ Convite inválido.", ephemeral=True)
            return

        await interaction.response.defer()

        async with get_session() as session:
            service = TribeService(session)
            
            # Verifica se quem convida é líder
            my_tribe, _ = await service.get_user_tribe(interaction.user.id)
            if not my_tribe or my_tribe.leader_id != interaction.user.id:
                await interaction.followup.send("❌ Apenas o líder da tribo pode enviar convites.")
                return

            # Verifica se o alvo já tem tribo
            target_tribe, _ = await service.get_user_tribe(membro.id)
            if target_tribe:
                await interaction.followup.send(f"❌ {membro.display_name} já pertence a uma tribo.")
                return

            # Adiciona direto (Para simplificar neste exemplo. O ideal seria um sistema de Aceitar/Recusar)
            await service.add_member(my_tribe.id, membro.id)
        
        await interaction.followup.send(f"🤝 **Bem-vindo!** {membro.mention} agora faz parte da tribo **{my_tribe.name}**.")

    @app_commands.command(name="tribo_sair", description="Sai da tua tribo atual.")
    async def tribo_sair(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = TribeService(session)
            tribe, _ = await service.get_user_tribe(interaction.user.id)
            
            if not tribe:
                await interaction.followup.send("❌ Não estás em nenhuma tribo.")
                return
                
            if tribe.leader_id == interaction.user.id:
                await interaction.followup.send("❌ O líder não pode sair. Dissolva a tribo ou passe a liderança (comando futuro).")
                return

            await service.remove_member(interaction.user.id)
            
        await interaction.followup.send(f"👋 Saíste da tribo **{tribe.name}**.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Tribes(bot))