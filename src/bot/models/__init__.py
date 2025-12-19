# Registra todos os modelos para o SQLModel saber o que criar
# Este arquivo é a "lista de chamada" para a criação do banco de dados.

from bot.models.user import User
from bot.models.goal import Goal
from bot.models.journal import JournalEntry
from bot.models.shop import ShopItem
from bot.models.habit import Habit
from bot.models.challenge import Challenge, ChallengeCompletion
from bot.models.library import LibraryResource
from bot.models.tribe import Tribe, TribeMember
from bot.models.mentorship import Mentorship
from bot.models.guild_config import GuildConfig
from bot.models.ticket import Ticket
from bot.models.giveaway import Giveaway
from bot.models.reaction_role import ReactionRole
from bot.models.reminder import Reminder
from bot.models.suggestion import Suggestion
from bot.models.poll import Poll
from bot.models.event import Event, EventParticipant
from bot.models.birthday import Birthday
from bot.models.starboard import StarboardConfig, StarboardEntry
from bot.models.networking import UserSkill
from bot.models.server_stats import StatChannel # <--- Garante que esta linha está aqui!
from bot.models.afk import AFKStatus
from bot.models.report import Report
from bot.models.feed import NewsFeed
from bot.models.level_reward import LevelReward
from bot.models.tag import Tag
from bot.models.confession import Confession
from bot.models.notification_config import NotificationConfig