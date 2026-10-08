from functools import lru_cache
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

NIVEIS_LOG = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class ErroConfiguracao(Exception):
    """config.yaml (ou logging.yaml) ausente, ilegível ou com valores inválidos."""


def _texto(config, secao, chave, problemas):
    valor = config.get(secao, {}).get(chave) if isinstance(config.get(secao), dict) else None
    if not isinstance(valor, str) or not valor.strip():
        problemas.append(f"'{secao}.{chave}' deve ser um texto não vazio")
    return valor


def validar_configuracao(config):
    # Junta todos os problemas para mostrar de uma vez, em vez de parar no primeiro.
    if not isinstance(config, dict):
        raise ErroConfiguracao("o config.yaml está vazio ou não tem o formato chave: valor")

    problemas = []
    _texto(config, "aplicacao", "nome", problemas)
    for chave in ("arquivos", "metadata", "exportacoes", "backups"):
        _texto(config, "diretorios", chave, problemas)
    _texto(config, "logging", "arquivo", problemas)

    limite = config.get("upload", {}).get("tamanho_maximo_mb") if isinstance(config.get("upload"), dict) else None
    # bool é subclasse de int no Python, por isso a exclusão explícita (true não é um tamanho).
    if not isinstance(limite, int) or isinstance(limite, bool) or limite <= 0:
        problemas.append("'upload.tamanho_maximo_mb' deve ser um número inteiro maior que zero")

    algoritmo = _texto(config, "hash", "algoritmo", problemas)
    if isinstance(algoritmo, str) and algoritmo != "sha256":
        problemas.append(f"'hash.algoritmo' não suportado: {algoritmo} (use sha256)")

    nivel = _texto(config, "logging", "nivel", problemas)
    if isinstance(nivel, str) and nivel.strip() and nivel.upper() not in NIVEIS_LOG:
        problemas.append(f"'logging.nivel' inválido: {nivel} (use {', '.join(sorted(NIVEIS_LOG))})")

    formato = _texto(config, "backup", "formato", problemas)
    if isinstance(formato, str) and formato.strip() and formato != "zip":
        problemas.append(f"'backup.formato' não suportado: {formato} (use zip)")

    if problemas:
        raise ErroConfiguracao("config.yaml inválido:\n  - " + "\n  - ".join(problemas))


# lru_cache guarda o resultado da primeira chamada: o config.yaml é lido uma
# única vez e todos os módulos passam a compartilhar o mesmo dicionário.
@lru_cache
def carregar_configuracao():
    caminho = BASE_DIR / "config.yaml"

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            config = yaml.safe_load(arquivo)
    except FileNotFoundError as erro:
        raise ErroConfiguracao(f"arquivo de configuração não encontrado: {caminho}") from erro
    except(OSError, UnicodeDecodeError) as erro:
        raise ErroConfiguracao(f"Erro ao ler config.yaml: {erro}") from erro
    except yaml.YAMLError as erro:
        raise ErroConfiguracao(f"O config.yaml contém YAML inválido: {erro}") from erro

    validar_configuracao(config)
    return config