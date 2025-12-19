import os
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Session, select, create_engine
from pydantic import BaseModel, ConfigDict # <--- Importação Nova
import uvicorn

# Adiciona o diretório raiz ao path para importar módulos do bot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Importações do Bot
from src.bot.config import settings
from src.bot.models.guild_config import GuildConfig

app = FastAPI(title="Dream Club API")

# Configuração do Banco
# Usamos o mesmo arquivo do bot
sqlite_url = settings.db_url.replace("sqlite+aiosqlite", "sqlite")
# check_same_thread=False é necessário para SQLite com FastAPI (threads diferentes)
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def get_session():
    with Session(engine) as session:
        yield session

# Modelo de Dados para validação da API
class ConfigUpdate(BaseModel):
    welcome_message_text: str
    module_welcome: bool
    module_economy: bool
    module_music: bool
    module_tickets: bool
    module_automod: bool
    
    # CORREÇÃO: Nova sintaxe do Pydantic V2
    model_config = ConfigDict(extra='ignore')

# --- API Endpoints ---

@app.get("/api/guild/{guild_id}")
async def get_guild_config(guild_id: int, session: Session = Depends(get_session)):
    stmt = select(GuildConfig).where(GuildConfig.guild_id == guild_id)
    config = session.exec(stmt).first()

    if not config:
        config = GuildConfig(guild_id=guild_id)
        session.add(config)
        session.commit()
        session.refresh(config)
    
    return config

@app.post("/api/guild/{guild_id}")
async def update_guild_config(guild_id: int, data: ConfigUpdate, session: Session = Depends(get_session)):
    stmt = select(GuildConfig).where(GuildConfig.guild_id == guild_id)
    config = session.exec(stmt).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Guild not found")

    config.welcome_message_text = data.welcome_message_text
    config.module_welcome = data.module_welcome
    config.module_economy = data.module_economy
    config.module_music = data.module_music
    config.module_tickets = data.module_tickets
    config.module_automod = data.module_automod
    
    session.add(config)
    session.commit()
    
    return {"status": "success", "message": "Configurações salvas!"}

# --- Servir Frontend ---

# Verifica se a pasta static existe antes de montar
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Retorna o index.html para qualquer rota não-API (SPA)
    index_path = os.path.join(static_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not found. Did you create src/web/static/index.html?"}

def start():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start()