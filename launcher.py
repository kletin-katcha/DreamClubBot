import subprocess
import sys
import os
import time
import json
import signal
from dotenv import load_dotenv

# Carrega as variáveis do .env
load_dotenv()

processes = []

def start_bot_process(profile_name):
    """Inicia uma instância do bot com um perfil específico."""
    print(f"🚀 [LAUNCHER] A iniciar Bot: {profile_name}...")
    
    env = os.environ.copy()
    env["BOT_PROFILE"] = profile_name
    
    p = subprocess.Popen(
        [sys.executable, "-m", "src.bot.main"],
        env=env,
        cwd=os.getcwd(),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(p)

def start_web_process():
    """Inicia o servidor do Dashboard Web."""
    print(f"🌐 [LAUNCHER] A iniciar Dashboard Web (Porta 8000)...")
    
    env = os.environ.copy()
    
    p = subprocess.Popen(
        [sys.executable, "src/web/api.py"],
        env=env,
        cwd=os.getcwd(),
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    processes.append(p)

def kill_all(*args):
    """Encerra todos os processos (Bots + Site)."""
    print("\n🛑 [LAUNCHER] A encerrar todos os sistemas...")
    for p in processes:
        if p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
    sys.exit(0)

def main():
    # Captura Ctrl+C para fechar tudo limpo
    signal.signal(signal.SIGINT, kill_all)
    signal.signal(signal.SIGTERM, kill_all)

    # Limpa o terminal (Windows/Linux)
    os.system('cls' if os.name == 'nt' else 'clear')

    print("╔══════════════════════════════════════════════════════════╗")
    print("║         GERENCIADOR DE SISTEMAS DREAM CLUB               ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    # 1. Iniciar o Bot Principal (MAIN)
    start_bot_process("MAIN")
    
    # Pausa para o Main iniciar o DB
    time.sleep(5) 

    # 2. Iniciar Bots de Música
    music_tokens_str = os.getenv("DISCORD_TOKENS_MUSICS", "[]")
    try:
        music_tokens = json.loads(music_tokens_str)
        count = len(music_tokens)
        
        if count > 0:
            print(f"\n🎵 [LAUNCHER] Carregando {count} módulos de áudio...")
            for i in range(count):
                profile = f"MUSIC_{i+1}"
                start_bot_process(profile)
                time.sleep(2)
    except:
        print("❌ [LAUNCHER] Erro ao ler tokens de música.")

    # 3. Iniciar o Dashboard Web
    print("\n🌍 [LAUNCHER] Carregando interface web...")
    start_web_process()

    # Mensagem Final
    print("\n" + "="*60)
    print("✅  SISTEMA OPERACIONAL COMPLETO")
    print("👉  Dashboard: http://localhost:8000")
    print("❌  Pressione Ctrl+C NESTA janela para desligar tudo.")
    print("="*60 + "\n")

    # Loop de Vigilância
    try:
        while True:
            time.sleep(1)
            # Verifica se algum processo morreu
            for p in list(processes):
                if p.poll() is not None:
                    # Opcional: Aqui poderiamos tentar reiniciar o processo automaticamente
                    print(f"⚠️ [LAUNCHER] Um processo encerrou inesperadamente (Código: {p.returncode}).")
                    processes.remove(p)
            
            if not processes:
                print("Todos os sistemas foram encerrados.")
                break
    except KeyboardInterrupt:
        kill_all()

if __name__ == "__main__":
    main()