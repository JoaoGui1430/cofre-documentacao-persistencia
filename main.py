from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.config import carregar_configuracao
from core.logging_config import configurar_logging
from core.repositorio import ErroPersistencia
from routers import backup, documentos, integridade, exportacoes

config = carregar_configuracao()
logger = configurar_logging(config)

app = FastAPI(
    title=config["aplicacao"]["nome"],
    description="API para armazenar e consultar por projeto e versão",
    version="0.0.1"
)

app.include_router(documentos.router)
app.include_router(integridade.router)
app.include_router(exportacoes.router)
app.include_router(backup.router)


# Qualquer falha ao ler/gravar o documentos.json vira uma resposta 500 e fica registrada no log.
@app.exception_handler(ErroPersistencia)
def tratar_erro_persistencia(request: Request, erro: ErroPersistencia):
    logger.error("ERRO_PERSISTENCIA %s", erro)
    return JSONResponse(status_code=500, content={"detail": "Erro ao acessar os metadados dos documentos"})


@app.get("/")
def home():
    return{"mensagem":"Cofre de documentação em funcionamento"}
