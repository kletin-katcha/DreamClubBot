import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.shop_service import ShopService

class Shop(commands.Cog):
    """
    Loja Oficial: Troque seus DreamCoins por Cargos.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="loja", description="Vê os itens disponíveis para compra com DC$.")
    async def loja(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with get_session() as session:
            service = ShopService(session)
            items = await service.list_items()

        if not items:
            await interaction.followup.send("🏪 A loja está vazia de momento.")
            return

        embed = discord.Embed(
            title="🏪 Loja Dream Club",
            description="Gaste seus DreamCoins (DC$) aqui.",
            color=discord.Color.green()
        )

        for item in items:
            role = interaction.guild.get_role(item.role_id)
            role_name = role.name if role else "Cargo Desconhecido"
            
            embed.add_field(
                name=f"📦 #{item.id} - {item.name}",
                value=f"💰 **Preço:** DC$ {item.price}\n📜 {item.description or 'Sem descrição'}\n🎖️ **Cargo:** {role_name}",
                inline=False
            )
        
        embed.set_footer(text="Use /comprar [id] para adquirir.")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="comprar", description="Compra um item da loja usando DC$.")
    @app_commands.describe(item_id="O ID do item")
    async def comprar(self, interaction: discord.Interaction, item_id: int):
        await interaction.response.defer()

        async with get_session() as session:
            service = ShopService(session)
            success, msg, item = await service.buy_item(interaction.user.id, item_id)

        if not success:
            await interaction.followup.send(f"❌ {msg}")
            return

        try:
            role = interaction.guild.get_role(item.role_id)
            if role:
                if role in interaction.user.roles:
                    await interaction.followup.send(f"⚠️ Compra feita, mas você já tinha o cargo **{role.name}**. Seus DC$ foram gastos.")
                else:
                    await interaction.user.add_roles(role, reason="Loja DreamCoins")
                    await interaction.followup.send(f"✅ **Sucesso!** Compraste **{item.name}** por DC$ {item.price}.")
            else:
                await interaction.followup.send(f"✅ Compra feita, mas o cargo não existe mais.")
        except discord.Forbidden:
            await interaction.followup.send("❌ Compra realizada, mas não consegui entregar o cargo (Permissões).")

    @app_commands.command(name="loja_admin_add", description="[Admin] Adiciona um item à loja.")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_add(self, interaction: discord.Interaction, nome: str, preco: int, cargo: discord.Role, descricao: str):
        await interaction.response.defer(ephemeral=True)
        
        async with get_session() as session:
            service = ShopService(session)
            await service.create_item(nome, preco, cargo.id, descricao)
            
        await interaction.followup.send(f"✅ Item **{nome}** criado! Preço: DC$ {preco}.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Shop(bot))