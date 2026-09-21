from fastapi import FastAPI

from core.config import carregar_configuracao
from core.logging_config import configurar_logging

config = carregar_configuracao()
logger = configurar_logging(config)

app = FastAPI(
    title=config["aplicacao"]["nome"],
    description="API para armazenar e consultar por projeto e versão",
    version="0.0.1"
)

@app.get("/")
def home():
    logger.info("Endpoint raiz acessado.")
    return{"mensagem":"Cofre de documentação em funcionamento"}