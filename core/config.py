from functools import lru_cache
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

# lru_cache guarda o resultado da primeira chamada: o config.yaml é lido uma
# única vez e todos os módulos passam a compartilhar o mesmo dicionário.
@lru_cache
def carregar_configuracao():
    caminho = BASE_DIR / "config.yaml"

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            config = yaml.safe_load(arquivo)
    except(OSError, UnicodeDecodeError) as erro:
        raise RuntimeError(f"Erro ao ler config.yaml: {erro}") from erro
    except yaml.YAMLError as erro:
        raise ValueError("O config.yaml contém YAML inválido") from erro


    return config