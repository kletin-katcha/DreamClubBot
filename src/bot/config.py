import os
import json
from typing import List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field

class Settings(BaseSettings):
    """
    Classe de configuração centralizada.
    """
    
    # --- Identidade do Bot ---
    # Define qual bot está rodando: 'MAIN', 'MUSIC_1', 'MUSIC_2', etc.
    bot_profile: str = Field(alias="BOT_PROFILE", default="MAIN", description="Perfil de execução do bot")

    # --- Tokens ---
    # Token do Bot Principal (Gestão, XP, Moderação)
    token_main: SecretStr = Field(alias="DISCORD_TOKEN_MAIN", default="", description="Token do Bot Principal")
    
    # Lista de Tokens para Bots de Música
    # No .env: DISCORD_TOKENS_MUSICS='["token1", "token2"]'
    tokens_music_json: str = Field(alias="DISCORD_TOKENS_MUSICS", default='[]', description="Lista JSON de tokens de música")

    # Compatibilidade (Fallback)
    token_fallback: SecretStr = Field(alias="DISCORD_TOKEN", default="", description="Token genérico")

    @property
    def music_tokens(self) -> List[str]:
        """Converte a string JSON do .env numa lista Python."""
        try:
            # Tenta decodificar o JSON da string
            tokens = json.loads(self.tokens_music_json)
            if isinstance(tokens, list):
                return tokens
            return []
        except json.JSONDecodeError:
            # Se não for JSON válido, tenta ver se é uma string simples (1 token)
            if self.tokens_music_json and self.tokens_music_json != '[]':
                return [self.tokens_music_json]
            return []

    @property
    def current_token(self) -> str:
        """
        Lógica inteligente para escolher o token.
        Se BOT_PROFILE="MUSIC_1", pega o índice 0 da lista.
        Se BOT_PROFILE="MUSIC_2", pega o índice 1 da lista.
        """
        profile = self.bot_profile.upper()

        # Lógica para Bots de Música (MUSIC_X)
        if profile.startswith("MUSIC_"):
            try:
                # Extrai o número do perfil (Ex: MUSIC_1 -> 1)
                parts = profile.split("_")
                if len(parts) < 2:
                    print(f"❌ Nome de perfil inválido: {profile}. Use MUSIC_1, MUSIC_2...")
                    return ""
                
                index = int(parts[1]) - 1 # Converte para índice (0-based)
                tokens = self.music_tokens
                
                if 0 <= index < len(tokens):
                    return tokens[index]
                else:
                    print(f"❌ Erro: Perfil {profile} pede o token #{index+1}, mas a lista só tem {len(tokens)} tokens.")
                    return ""
            except ValueError:
                print(f"❌ Erro ao ler índice do perfil {profile}.")
                return ""
        
        # Padrão: MAIN
        val = self.token_main.get_secret_value()
        # Se não tiver token main específico, tenta o fallback
        return val if val else self.token_fallback.get_secret_value()

    # --- Configurações Gerais ---
    command_prefix: str = Field(default="!", description="Prefixo para comandos de texto")
    log_level: str = Field(default="INFO", description="Nível de log")
    
    # Banco de Dados
    db_url: str = Field(alias="POSTGRES_URL", default="sqlite+aiosqlite:///bot.db")

    # Lavalink Nodes
    lavalink_nodes_json: str = Field(
        alias="LAVALINK_NODES",
        default='['
                '{"identifier": "🏠 Local", "uri": "http://localhost:2333", "password": "youshallnotpass"},'
                '{"identifier": "🌍 Public Host", "uri": "https://lavalink.host:443", "password": "youshallnotpass"},'
                '{"identifier": "🌍 Public KTech", "uri": "https://lavalink.ktechs.top:443", "password": "youshallnotpass"}'
                ']'
    )

    @property
    def lavalink_nodes(self) -> List[Dict[str, Any]]:
        try:
            nodes = json.loads(self.lavalink_nodes_json)
            if not isinstance(nodes, list): return []
            return nodes
        except: return []

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

try:
    settings = Settings()
except Exception as e:
    print(f"Erro crítico de configuração: {e}")
    exit(1)