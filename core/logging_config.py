import logging
import logging.config
import yaml

from core.config import BASE_DIR

def configurar_logging(config):
    caminho = BASE_DIR / "logging.yaml"

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            config_logging = yaml.safe_load(arquivo)

    except (OSError, UnicodeDecodeError) as erro:
        raise RuntimeError(f"Erro ao ler logging.yaml: {erro}") from erro
    except yaml.YAMLError as erro:
        raise ValueError("O logging.yaml contém YAML inválido.") from erro

    diretorio_logs = BASE_DIR / config["diretorios"]["logs"]

    diretorio_logs.mkdir(parents=True, exist_ok=True)

    nome_arquivo = config_logging["handlers"]["file"]["filename"]

    config_logging["handlers"]["file"]["filename"] = str(diretorio_logs / nome_arquivo)

    logging.config.dictConfig(config_logging)
    
    logger = logging.getLogger("cofre_api")
    logger.info("Sistema de logging inicializado")

    return logger