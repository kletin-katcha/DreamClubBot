import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import html
import random
import asyncio
from bot.core.database import get_session
from bot.services.user_service import UserService
from deep_translator import GoogleTranslator

class QuizButton(discord.ui.Button):
    """Botão de resposta do Quiz."""
    def __init__(self, label: str, is_correct: bool):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.is_correct = is_correct

    async def callback(self, interaction: discord.Interaction):
        view: QuizView = self.view
        
        for child in view.children:
            child.disabled = True
            if child.is_correct:
                child.style = discord.ButtonStyle.success
            elif child == self and not self.is_correct:
                child.style = discord.ButtonStyle.danger
        
        view.stop()
        
        if self.is_correct:
            async with get_session() as session:
                service = UserService(session)
                leveled_up = await service.add_xp(interaction.user.id, view.xp_reward)
                
            msg = f"✅ **Correto!** Ganhaste **{view.xp_reward} XP** de sabedoria."
            if leveled_up: msg += "\n🏆 **SUBIU DE NÍVEL!**"
        else:
            msg = "❌ **Errado!** Mais sorte na próxima vez."

        await interaction.response.edit_message(content=msg, view=view)

class QuizView(discord.ui.View):
    """Container dos botões do Quiz."""
    def __init__(self, correct_answer: str, incorrect_answers: list, xp_reward: int, user_id: int):
        super().__init__(timeout=45) # Aumentei um pouco o tempo pois a leitura traduzida pode demorar
        self.xp_reward = xp_reward
        self.user_id = user_id
        
        all_answers = incorrect_answers + [correct_answer]
        random.shuffle(all_answers)
        
        for ans in all_answers:
            clean_label = html.unescape(ans)
            if len(clean_label) > 80: clean_label = clean_label[:77] + "..."
            self.add_item(QuizButton(clean_label, ans == correct_answer))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Inicie o seu próprio quiz com `/quiz`.", ephemeral=True)
            return False
        return True
    
    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

class Quiz(commands.Cog):
    """
    Minigame de Perguntas e Respostas (Traduzido).
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Instancia o tradutor
        self.translator = GoogleTranslator(source='auto', target='pt')

    def translate_data(self, category, question, correct, incorrect_list):
        """
        Função síncrona para traduzir os textos.
        Deve ser rodada num executor para não bloquear o bot.
        """
        try:
            t_category = self.translator.translate(category)
            t_question = self.translator.translate(question)
            t_correct = self.translator.translate(correct)
            t_incorrect = [self.translator.translate(ans) for ans in incorrect_list]
            return t_category, t_question, t_correct, t_incorrect
        except Exception as e:
            # Em caso de falha na tradução, retorna o original
            print(f"Erro na tradução: {e}")
            return category, question, correct, incorrect_list

    @app_commands.command(name="quiz", description="Teste seu conhecimento (PT-BR) e ganhe XP.")
    @app_commands.describe(dificuldade="Nível das perguntas")
    @app_commands.choices(dificuldade=[
        app_commands.Choice(name="Fácil (20 XP)", value="easy"),
        app_commands.Choice(name="Médio (50 XP)", value="medium"),
        app_commands.Choice(name="Difícil (100 XP)", value="hard"),
    ])
    async def quiz(self, interaction: discord.Interaction, dificuldade: app_commands.Choice[str] = None):
        await interaction.response.defer()
        
        diff_value = dificuldade.value if dificuldade else "medium"
        xp_map = {"easy": 20, "medium": 50, "hard": 100}
        xp_reward = xp_map.get(diff_value, 20)

        # 1. Busca pergunta em Inglês (OpenTDB)
        url = f"https://opentdb.com/api.php?amount=1&type=multiple&difficulty={diff_value}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("❌ Erro ao conectar ao banco de questões.")
                    return
                data = await resp.json()

        if data["response_code"] != 0:
            await interaction.followup.send("❌ Não encontrei perguntas com esses critérios.")
            return

        q_data = data["results"][0]
        
        # 2. Prepara dados brutos
        raw_category = html.unescape(q_data["category"])
        raw_question = html.unescape(q_data["question"])
        raw_correct = html.unescape(q_data["correct_answer"])
        raw_incorrect = [html.unescape(ans) for ans in q_data["incorrect_answers"]]

        # 3. Traduz (Executa em background para não travar o bot)
        t_category, t_question, t_correct, t_incorrect = await self.bot.loop.run_in_executor(
            None, 
            self.translate_data, 
            raw_category, raw_question, raw_correct, raw_incorrect
        )

        # 4. Envia
        embed = discord.Embed(
            title="🧠 Desafio de Conhecimento",
            description=f"**Categoria:** {t_category}\n**Dificuldade:** {diff_value.title()}\n**Recompensa:** {xp_reward} XP",
            color=discord.Color.teal()
        )
        embed.add_field(name="Pergunta:", value=f"*{t_question}*", inline=False)
        embed.set_footer(text="Tens 45 segundos para responder.")

        view = QuizView(t_correct, t_incorrect, xp_reward, interaction.user.id)
        await interaction.followup.send(embed=embed, view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(Quiz(bot))