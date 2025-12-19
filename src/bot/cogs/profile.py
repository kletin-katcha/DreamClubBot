import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.user_service import UserService
from bot.services.level_service import LevelService
from bot.utils.embeds import EmbedFactory, DreamColors
import logging

logger = logging.getLogger(__name__)

class Profile(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def check_level_rewards(self, member: discord.Member, new_level: int):
        async with get_session() as session:
            lvl_service = LevelService(session)
            rewards = await lvl_service.get_rewards_for_level(member.guild.id, new_level)
            
            if not rewards: return

            roles_added = []
            for r in rewards:
                role = member.guild.get_role(r.role_id)
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role, reason=f"Level Up: {new_level}")
                        roles_added.append(role.name)
                    except discord.Forbidden:
                        logger.warning(f"Sem permissão para dar cargo {role.name}")

            if roles_added:
                try:
                    role_names = ", ".join(roles_added)
                    embed = EmbedFactory.create(
                        title="🎉 Recompensas Desbloqueadas!",
                        description=f"Ao atingir o nível **{new_level}**, ganhaste:\n**{role_names}**",
                        color=discord.Color.gold(),
                        footer=f"Servidor: {member.guild.name}"
                    )
                    await member.send(embed=embed)
                except: pass

    @app_commands.command(name="perfil", description="Veja seu nível de maturidade e progresso.")
    async def perfil(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            user_db = await service.get_profile(target.id)

        xp_next = user_db.proximo_nivel_xp
        progress_pct = user_db.xp_maturidade / xp_next
        blocks = int(progress_pct * 10)
        progress_bar = "█" * blocks + "░" * (10 - blocks)

        # USANDO A FÁBRICA
        embed = EmbedFactory.create(
            title=f"🛡️ Perfil de {target.display_name}",
            color=DreamColors.INFO,
            thumbnail=target.display_avatar.url,
            footer="Dica: Use /bio para definir sua frase."
        )
        
        embed.add_field(name="Nível", value=f"` {user_db.nivel} `", inline=True)
        embed.add_field(name="XP Atual", value=f"` {user_db.xp_maturidade} / {xp_next} `", inline=True)
        embed.add_field(name="DreamCoins", value=f"DC$ {user_db.dream_coins}", inline=True)
        embed.add_field(name="Progresso", value=f"[{progress_bar}] {int(progress_pct * 100)}%", inline=False)
        
        if user_db.bio_estoica:
            embed.add_field(name="📜 Bio", value=f"*{user_db.bio_estoica}*", inline=False)

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="bio", description="Defina uma frase estoica ou de foco para seu perfil.")
    @app_commands.describe(texto="Sua frase pessoal (máx 200 caracteres)")
    async def bio(self, interaction: discord.Interaction, texto: str):
        if len(texto) > 200:
            await interaction.response.send_message(embed=EmbedFactory.error("A bio deve ter no máximo 200 caracteres."), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = UserService(session)
            await service.update_bio(interaction.user.id, texto)

        embed = EmbedFactory.success(f"**Nova Bio:**\n> *{texto}*")
        await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))