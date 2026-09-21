from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent

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