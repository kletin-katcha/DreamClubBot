import os
import time

db_file = "bot.db"

print(f"Tentando apagar {db_file}...")

if os.path.exists(db_file):
    try:
        os.remove(db_file)
        print(f"✅ SUCESSO: O arquivo {db_file} foi apagado.")
        print("Agora você pode rodar o bot e ele criará todas as tabelas novas!")
    except PermissionError:
        print(f"❌ ERRO: O arquivo {db_file} está em uso.")
        print("⚠️ FECHE todos os terminais python, VS Code ou DB Browser que estejam usando o arquivo.")
    except Exception as e:
        print(f"❌ Erro desconhecido: {e}")
else:
    print(f"⚠️ O arquivo {db_file} não existe (o que é bom!). Pode iniciar o bot.")