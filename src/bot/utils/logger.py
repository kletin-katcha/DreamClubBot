import logging
import sys

class TermColors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Cores de Texto
    GRAY = "\033[90m"
    WHITE = "\033[97m"
    CYAN = "\033[36m"
    PURPLE = "\033[35m"
    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    RED = "\033[31m"

    # Níveis de Log (Background ou Texto forte)
    bg_DEBUG = "\033[37m"     # Branco
    bg_INFO = "\033[94m"      # Azul Claro
    bg_WARNING = "\033[93m"   # Amarelo
    bg_ERROR = "\033[91m"     # Vermelho
    bg_CRITICAL = "\033[41m\033[97m" # Fundo Vermelho, Texto Branco

class ColoredFormatter(logging.Formatter):
    """
    Substitui o formato padrão chato por um formato colorido e alinhado.
    Formato: [HORA] [NÍVEL] [MÓDULO] Mensagem
    """
    
    def __init__(self):
        # Formato base: Hora em cinza, o resto configurável
        self.time_fmt = f"{TermColors.GRAY}%(asctime)s{TermColors.RESET}"
        
        # Formatos para cada nível
        self.FORMATS = {
            logging.DEBUG:    f"{self.time_fmt} {TermColors.bg_DEBUG} DBG {TermColors.RESET} {TermColors.GRAY}%(name)-15s{TermColors.RESET} %(message)s",
            logging.INFO:     f"{self.time_fmt} {TermColors.bg_INFO} INF {TermColors.RESET} {TermColors.PURPLE}%(name)-15s{TermColors.RESET} %(message)s",
            logging.WARNING:  f"{self.time_fmt} {TermColors.bg_WARNING} WRN {TermColors.RESET} {TermColors.YELLOW}%(name)-15s{TermColors.RESET} %(message)s",
            logging.ERROR:    f"{self.time_fmt} {TermColors.bg_ERROR} ERR {TermColors.RESET} {TermColors.RED}%(name)-15s{TermColors.RESET} %(message)s",
            logging.CRITICAL: f"{self.time_fmt} {TermColors.bg_CRITICAL} CRT {TermColors.RESET} {TermColors.RED}%(name)-15s{TermColors.RESET} %(message)s",
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

def setup_logger():
    """Configura o logger raiz para usar o nosso formatador."""
    # Cria o handler para o console (stdout)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter())

    # Configura o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove handlers antigos (evita logs duplicados)
    if root_logger.handlers:
        root_logger.handlers = []
    
    root_logger.addHandler(handler)

    # Silencia logs chatos de bibliotecas externas
    logging.getLogger("discord.gateway").setLevel(logging.WARNING)
    logging.getLogger("discord.client").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)