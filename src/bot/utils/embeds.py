import discord
import datetime
from typing import Optional, Union

class DreamColors:
    """Paleta de cores padrão do Dream Club."""
    DEFAULT = discord.Color.from_rgb(147, 112, 219) # Roxo Médio (Dream)
    SUCCESS = discord.Color.from_rgb(87, 242, 135)  # Verde
    ERROR = discord.Color.from_rgb(237, 66, 69)     # Vermelho
    WARNING = discord.Color.from_rgb(254, 231, 92)  # Amarelo
    INFO = discord.Color.from_rgb(88, 101, 242)     # Azul Blurple

class EmbedFactory:
    """
    Fábrica centralizada para criação de Embeds consistentes.
    """

    @staticmethod
    def create(
        title: str = None,
        description: str = None,
        color: discord.Color = DreamColors.DEFAULT,
        footer: str = "Dream Club • Evolução Constante",
        thumbnail: str = None,
        image: str = None,
        author: Union[discord.User, discord.Member] = None
    ) -> discord.Embed:
        """Cria um embed genérico base."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.datetime.utcnow()
        )
        
        if footer:
            embed.set_footer(text=footer)
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
            
        if image:
            embed.set_image(url=image)
            
        if author:
            embed.set_author(name=author.display_name, icon_url=author.display_avatar.url)
            
        return embed

    @staticmethod
    def success(description: str, title: str = "✅ Sucesso") -> discord.Embed:
        """Gera um embed verde de sucesso rápido."""
        return EmbedFactory.create(title=title, description=description, color=DreamColors.SUCCESS)

    @staticmethod
    def error(description: str, title: str = "❌ Erro") -> discord.Embed:
        """Gera um embed vermelho de erro rápido."""
        return EmbedFactory.create(title=title, description=description, color=DreamColors.ERROR)

    @staticmethod
    def warning(description: str, title: str = "⚠️ Atenção") -> discord.Embed:
        """Gera um embed amarelo de aviso."""
        return EmbedFactory.create(title=title, description=description, color=DreamColors.WARNING)