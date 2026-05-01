import os
import sys
from dotenv import load_dotenv


def _find_dotenv() -> str:
    if getattr(sys, 'frozen', False):
        # Rodando como .exe — procura o .env na mesma pasta do executável
        return os.path.join(os.path.dirname(sys.executable), '.env')
    # Rodando como script — procura na pasta config/
    return os.path.join(os.path.dirname(__file__), '.env')


def _get_base_dir() -> str:
    """Pasta do .exe (quando frozen) ou raiz do projeto (quando script)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


load_dotenv(_find_dotenv())

URL_PORTO = os.getenv("URL_PORTO_SEGURO")

CREDENCIAIS = [
    {"cpf": os.getenv("PORTO_CPF_1"), "senha": os.getenv("PORTO_SENHA_1")},
    {"cpf": os.getenv("PORTO_CPF_2"), "senha": os.getenv("PORTO_SENHA_2")},
]

# Caminho de saída — sempre relativo ao .exe ou à raiz do projeto
OUTPUT_DIR = os.path.join(_get_base_dir(), "dados")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "base_de_extracao.xlsx")
