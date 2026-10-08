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

    arquivo_log = BASE_DIR / config["logging"]["arquivo"]

    arquivo_log.parent.mkdir(parents=True, exist_ok=True)

    config_logging["handlers"]["file"]["filename"] = str(arquivo_log)
    config_logging["loggers"]["cofre_api"]["level"] = str(config["logging"]["nivel"]).upper()

    logging.config.dictConfig(config_logging)
    
    logger = logging.getLogger("cofre_api")
    logger.info("INICIALIZACAO aplicacao=\"%s\" log=%s", config["aplicacao"]["nome"], config_logging["handlers"]["file"]["filename"])

    return logger