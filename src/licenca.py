import os
import sys
import json
import uuid
import hmac
import base64
import hashlib
import platform
from datetime import datetime, timezone
from config.settings import _find_dotenv
from dotenv import load_dotenv

# ─── Carregar variáveis de ambiente ───────────────────────────────────────
load_dotenv(_find_dotenv())

# ─── Configuração ────────────────────────────────────────────────────────────
TRIAL_DAYS = 3

# ⚠️ Segredo agora vem do .env (não hardcoded!)
_SECRET = os.getenv("PS_SECRET", "change_me_in_env")

_APPDATA_DIR = os.path.join(os.environ.get("APPDATA", ""), "RoboPortoSeguro")
_TRIAL_FILE  = os.path.join(_APPDATA_DIR, ".session")

CONTATO = (
    "Para adquirir a licença completa, entre em contato:\n\n"
    "WhatsApp: (XX) XXXXX-XXXX\n"
    "E-mail:   seuemail@email.com"
)
# ─────────────────────────────────────────────────────────────────────────────


def _exe_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_machine_id() -> str:
    """Gera um ID único de 16 chars baseado no hardware da máquina."""
    mac       = str(uuid.getnode())
    hostname  = platform.node()
    processor = platform.processor()
    raw = f"{mac}|{hostname}|{processor}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16].upper()


def gerar_chave_para_maquina(machine_id: str) -> str:
    """Gera a chave de licença vinculada ao ID de máquina (formato XXXX-XXXX-XXXX-XXXX)."""
    h = hmac.new(_SECRET.encode(), machine_id.upper().encode(), hashlib.sha256).hexdigest()[:16].upper()
    return f"{h[0:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"


def _assinar(dados: str) -> str:
    return hmac.new(_SECRET.encode(), dados.encode(), hashlib.sha256).hexdigest()


def _ler_trial_start() -> datetime | None:
    """Retorna a data de início do trial, ou None se não existir/corrompido."""
    if not os.path.exists(_TRIAL_FILE):
        return None
    try:
        raw  = base64.b64decode(open(_TRIAL_FILE, 'rb').read()).decode()
        data = json.loads(raw)
        ts       = data.get("start", "")
        checksum = data.get("checksum", "")
        if checksum != _assinar(ts):
            return None  # arquivo adulterado
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _criar_trial():
    """Registra o início do trial."""
    os.makedirs(_APPDATA_DIR, exist_ok=True)
    ts   = datetime.now(timezone.utc).isoformat()
    data = {"start": ts, "checksum": _assinar(ts)}
    raw  = base64.b64encode(json.dumps(data).encode())
    with open(_TRIAL_FILE, 'wb') as f:
        f.write(raw)


def _dias_de_trial() -> int:
    """Retorna quantos dias se passaram desde o início do trial."""
    inicio = _ler_trial_start()
    if inicio is None:
        _criar_trial()
        return 0
    agora = datetime.now(timezone.utc)
    return (agora - inicio).days


def ativar_licenca(chave: str) -> bool:
    """
    Valida a chave para esta máquina e salva license.dat se válida.
    Retorna True em caso de sucesso.
    """
    machine_id = get_machine_id()
    chave_esperada = gerar_chave_para_maquina(machine_id)
    if chave.strip().upper() == chave_esperada:
        license_path = os.path.join(_exe_dir(), "license.dat")
        data = {"machine_id": machine_id, "key": chave.strip().upper()}
        checksum = _assinar(f"{machine_id}:{chave.strip().upper()}")
        data["checksum"] = checksum
        with open(license_path, 'w') as f:
            json.dump(data, f)
        return True
    return False


def _verificar_license_dat() -> bool:
    """Retorna True se license.dat existe e é válido para esta máquina."""
    license_path = os.path.join(_exe_dir(), "license.dat")
    if not os.path.exists(license_path):
        return False
    try:
        data       = json.load(open(license_path))
        machine_id = data.get("machine_id", "")
        chave      = data.get("key", "")
        checksum   = data.get("checksum", "")
        if machine_id != get_machine_id():
            return False
        if checksum != _assinar(f"{machine_id}:{chave}"):
            return False
        return gerar_chave_para_maquina(machine_id) == chave
    except Exception:
        return False


def verificar() -> dict:
    """
    Verifica o status da licença e retorna um dicionário:
      {"status": "full"}
      {"status": "trial", "dias_restantes": N}
      {"status": "expirado", "machine_id": "XXXX..."}
      {"status": "licenca_invalida"}
    """
    if _verificar_license_dat():
        return {"status": "full"}

    machine_id = get_machine_id()
    dias = _dias_de_trial()

    restantes = TRIAL_DAYS - dias
    if restantes > 0:
        return {"status": "trial", "dias_restantes": restantes}

    return {"status": "expirado", "machine_id": machine_id}
