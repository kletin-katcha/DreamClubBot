import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.networking_service import NetworkingService

class Networking(commands.Cog):
    """
    Conecte-se com membros através de habilidades e interesses.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="skill_add", description="Adicione uma competência ao seu perfil (Ex: Design, Python).")
    @app_commands.describe(habilidade="Nome da habilidade (Máx 20 letras)")
    async def skill_add(self, interaction: discord.Interaction, habilidade: str):
        if len(habilidade) > 20:
            await interaction.response.send_message("❌ Nome muito longo. Seja conciso.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = NetworkingService(session)
            result = await service.add_skill(interaction.user.id, habilidade)
            
        if result:
            await interaction.followup.send(f"✅ Habilidade **#{habilidade.lower()}** adicionada ao seu perfil!")
        else:
            await interaction.followup.send("⚠️ Erro: Ou você já tem essa habilidade ou atingiu o limite de 10.")

    @app_commands.command(name="skill_remove", description="Remove uma competência do perfil.")
    async def skill_remove(self, interaction: discord.Interaction, habilidade: str):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = NetworkingService(session)
            success = await service.remove_skill(interaction.user.id, habilidade)
            
        if success:
            await interaction.followup.send(f"🗑️ Habilidade **#{habilidade.lower()}** removida.")
        else:
            await interaction.followup.send("❌ Habilidade não encontrada no seu perfil.")

    @app_commands.command(name="perfil_skills", description="Vê as habilidades de um membro.")
    async def perfil_skills(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        await interaction.response.defer()
        
        async with get_session() as session:
            service = NetworkingService(session)
            skills = await service.get_user_skills(target.id)
            
        if not skills:
            msg = f"{target.display_name} ainda não registou habilidades."
            await interaction.followup.send(msg)
            return

        # Formata tags bonitas (Ex: `Python` `Design`)
        tags = " ".join([f"`#{s.title()}`" for s in skills])
        
        embed = discord.Embed(
            title=f"🧠 Expertise: {target.display_name}",
            description=tags,
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="networking", description="Encontra pessoas no servidor com uma habilidade.")
    async def networking(self, interaction: discord.Interaction, busca: str):
        await interaction.response.defer()
        
        async with get_session() as session:
            service = NetworkingService(session)
            user_ids = await service.search_users_by_skill(busca)
            
        if not user_ids:
            await interaction.followup.send(f"🔍 Ninguém encontrado com a habilidade **{busca}**.")
            return

        # Filtra apenas membros que estão no servidor atual
        found_members = []
        for uid in user_ids:
            member = interaction.guild.get_member(uid)
            if member:
                found_members.append(member.mention)
        
        if not found_members:
            await interaction.followup.send(f"🔍 Encontrei utilizadores, mas eles não estão neste servidor.")
            return

        # Limita visualização para não spammar
        display = ", ".join(found_members[:20])
        if len(found_members) > 20:
            display += f" e mais {len(found_members)-20}..."

        embed = discord.Embed(
            title=f"🤝 Networking: {busca.title()}",
            description=f"Encontrei **{len(found_members)}** especialistas:\n\n{display}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Networking(bot))