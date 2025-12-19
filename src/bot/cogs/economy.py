import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.user_service import UserService
import random

class Economy(commands.Cog):
    """
    Sistema financeiro (Transferências e Apostas com DreamCoins).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="saldo", description="Vê quanto tens na carteira.")
    async def saldo(self, interaction: discord.Interaction, membro: discord.Member = None):
        target = membro or interaction.user
        await interaction.response.defer()
        
        async with get_session() as session:
            service = UserService(session)
            user = await service.get_profile(target.id)
            
        await interaction.followup.send(f"💰 **Carteira de {target.display_name}:**\nDC$ {user.dream_coins}")

    @app_commands.command(name="pagar", description="Transfere DreamCoins para outro membro.")
    @app_commands.describe(membro="Quem vai receber", valor="Quantidade de DC$")
    async def pagar(self, interaction: discord.Interaction, membro: discord.Member, valor: int):
        if membro.id == interaction.user.id:
            await interaction.response.send_message("❌ Você não pode pagar a si mesmo.", ephemeral=True)
            return
        
        if valor <= 0:
            await interaction.response.send_message("❌ O valor deve ser positivo.", ephemeral=True)
            return

        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            success = await service.transfer_coins(interaction.user.id, membro.id, valor)

            if success:
                await interaction.followup.send(f"💸 **Transferência Concluída!**\n{interaction.user.mention} enviou **DC$ {valor}** para {membro.mention}.")
            else:
                await interaction.followup.send("❌ Saldo insuficiente em DreamCoins.")

    @app_commands.command(name="cara_coroa", description="Aposte DC$ no Cara ou Coroa (Dobro ou Nada).")
    @app_commands.choices(escolha=[
        app_commands.Choice(name="Cara", value="cara"),
        app_commands.Choice(name="Coroa", value="coroa")
    ])
    async def cara_coroa(self, interaction: discord.Interaction, valor: int, escolha: app_commands.Choice[str]):
        if valor < 10:
            await interaction.response.send_message("❌ Aposta mínima é DC$ 10.", ephemeral=True)
            return

        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            # Verifica saldo
            user = await service.get_profile(interaction.user.id)
            if user.dream_coins < valor:
                await interaction.followup.send("❌ Você não tem DreamCoins suficientes para essa aposta.")
                return

            resultado = random.choice(["cara", "coroa"])
            ganhou = (resultado == escolha.value)

            if ganhou:
                await service.add_coins(interaction.user.id, valor)
                color = discord.Color.green()
                msg = f"🎉 **Vitória!** Deu **{resultado.title()}**.\nGanhaste **DC$ {valor}**!"
            else:
                await service.remove_coins(interaction.user.id, valor)
                color = discord.Color.red()
                msg = f"📉 **Derrota...** Deu **{resultado.title()}**.\nPerdeste **DC$ {valor}**."

            embed = discord.Embed(title="🪙 Cara ou Coroa", description=msg, color=color)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="dado", description="Role um dado. Aposte DC$.")
    async def dado(self, interaction: discord.Interaction, valor: int):
        if valor < 10:
            await interaction.response.send_message("❌ Aposta mínima é DC$ 10.", ephemeral=True)
            return

        await interaction.response.defer()

        async with get_session() as session:
            service = UserService(session)
            user = await service.get_profile(interaction.user.id)
            
            if user.dream_coins < valor:
                await interaction.followup.send("❌ Saldo insuficiente.")
                return

            lado = random.randint(1, 6)
            
            # Regra: 1-3 Perde | 4-6 Ganha
            if lado >= 4:
                lucro = int(valor * 0.5) # Ganha 50% de lucro
                await service.add_coins(interaction.user.id, lucro)
                msg = f"🎲 O dado caiu em **{lado}**!\n**Você venceu!** Lucro de **DC$ {lucro}**."
                color = discord.Color.green()
            else:
                await service.remove_coins(interaction.user.id, valor)
                msg = f"🎲 O dado caiu em **{lado}**...\n**Você perdeu** DC$ {valor}."
                color = discord.Color.red()

            embed = discord.Embed(description=msg, color=color)
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))