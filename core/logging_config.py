import logging
import logging.config
import yaml

from core.config import BASE_DIR, ErroConfiguracao

def configurar_logging(config):
    caminho = BASE_DIR / "logging.yaml"

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            config_logging = yaml.safe_load(arquivo)

    except FileNotFoundError as erro:
        raise ErroConfiguracao(f"arquivo de configuração de log não encontrado: {caminho}") from erro
    except (OSError, UnicodeDecodeError) as erro:
        raise ErroConfiguracao(f"Erro ao ler logging.yaml: {erro}") from erro
    except yaml.YAMLError as erro:
        raise ErroConfiguracao(f"O logging.yaml contém YAML inválido: {erro}") from erro

    arquivo_log = BASE_DIR / config["logging"]["arquivo"]

    try:
        arquivo_log.parent.mkdir(parents=True, exist_ok=True)

        config_logging["handlers"]["file"]["filename"] = str(arquivo_log)
        config_logging["loggers"]["cofre_api"]["level"] = str(config["logging"]["nivel"]).upper()

        logging.config.dictConfig(config_logging)
    except (TypeError, KeyError) as erro:
        raise ErroConfiguracao(f"O logging.yaml não tem a estrutura esperada (faltando: {erro})") from erro
    except (OSError, ValueError) as erro:
        raise ErroConfiguracao(f"Não foi possível configurar o log em {arquivo_log}: {erro}") from erro
    
    logger = logging.getLogger("cofre_api")
    logger.info("INICIALIZACAO aplicacao=\"%s\" log=%s", config["aplicacao"]["nome"], config_logging["handlers"]["file"]["filename"])

    return logger