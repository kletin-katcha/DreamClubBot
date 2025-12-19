import discord
from discord import app_commands
from discord.ext import commands
from bot.core.database import get_session
from bot.services.poll_service import PollService

class Polls(commands.Cog):
    """
    Sistema de votação e enquetes.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Emojis numéricos para até 10 opções
        self.emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @app_commands.command(name="enquete", description="Cria uma votação pública.")
    @app_commands.describe(pergunta="Qual é a questão?", opcoes="Separe as opções com a barra vertical | (Ex: Pizza|Hambúrguer|Salada)")
    async def enquete(self, interaction: discord.Interaction, pergunta: str, opcoes: str):
        # Separa as opções
        options_list = [opt.strip() for opt in opcoes.split("|") if opt.strip()]
        
        if len(options_list) < 2:
            await interaction.response.send_message("❌ Você precisa de pelo menos 2 opções separadas por `|`.", ephemeral=True)
            return
        
        if len(options_list) > 10:
            await interaction.response.send_message("❌ O limite máximo é de 10 opções.", ephemeral=True)
            return

        await interaction.response.defer()

        # Monta o texto visual das opções
        description = ""
        for i, option in enumerate(options_list):
            description += f"{self.emojis[i]} **{option}**\n\n"

        embed = discord.Embed(
            title=f"📊 {pergunta}",
            description=description,
            color=discord.Color.gold()
        )
        embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text="Reaja abaixo para votar!")

        message = await interaction.followup.send(embed=embed)

        # Adiciona as reações correspondentes
        for i in range(len(options_list)):
            await message.add_reaction(self.emojis[i])

        # Salva no banco
        async with get_session() as session:
            service = PollService(session)
            await service.create_poll(
                interaction.guild.id,
                interaction.channel.id,
                message.id,
                interaction.user.id,
                pergunta,
                opcoes
            )

    @app_commands.command(name="enquete_encerrar", description="Finaliza uma enquete e mostra o resultado.")
    @app_commands.describe(id_mensagem="ID da mensagem da enquete (Ative o Modo Desenvolvedor do Discord para pegar)")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def enquete_encerrar(self, interaction: discord.Interaction, id_mensagem: str):
        try:
            msg_id = int(id_mensagem)
        except:
            await interaction.response.send_message("❌ ID inválido.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        async with get_session() as session:
            service = PollService(session)
            poll = await service.close_poll(msg_id)

            if not poll:
                await interaction.followup.send("❌ Enquete não encontrada ou já encerrada.")
                return

            # Busca a mensagem para contar votos
            try:
                channel = interaction.guild.get_channel(poll.channel_id)
                message = await channel.fetch_message(poll.message_id)
            except:
                await interaction.followup.send("❌ Não consegui encontrar a mensagem original da enquete.")
                return

            # Contagem
            options_list = poll.options.split("|")
            results = []
            total_votes = 0
            
            # Itera sobre as reações da mensagem
            for reaction in message.reactions:
                if str(reaction.emoji) in self.emojis:
                    index = self.emojis.index(str(reaction.emoji))
                    if index < len(options_list):
                        # Subtrai 1 porque o bot conta como 1 voto
                        count = reaction.count - 1 
                        results.append((options_list[index], count))
                        total_votes += count

            # Ordena por mais votado
            results.sort(key=lambda x: x[1], reverse=True)

            # Gera relatório
            report = f"**Pergunta:** {poll.question}\n\n"
            for opt, count in results:
                pct = (count / total_votes * 100) if total_votes > 0 else 0
                bar = "█" * int(pct / 10)
                report += f"**{opt}**: {count} votos ({int(pct)}%)\n`{bar}`\n"

            report += f"\n👥 **Total de Votos:** {total_votes}"

            # Atualiza a mensagem original para "Encerrada"
            original_embed = message.embeds[0]
            original_embed.color = discord.Color.greyple()
            original_embed.set_footer(text="🔴 Enquete Encerrada")
            await message.edit(embed=original_embed)

            # Envia resultado no chat
            result_embed = discord.Embed(
                title="📊 Resultado da Enquete",
                description=report,
                color=discord.Color.green()
            )
            await channel.send(embed=result_embed)
            await interaction.followup.send("✅ Enquete encerrada com sucesso!")

async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))