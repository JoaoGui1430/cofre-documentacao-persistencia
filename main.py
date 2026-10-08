import sys

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from core.config import ErroConfiguracao, carregar_configuracao
from core.logging_config import configurar_logging

# Config inválida: mostra uma mensagem clara e encerra, em vez de um traceback.
# Precisa vir antes de importar os routers, porque eles já leem a configuração ao serem importados.
try:
    config = carregar_configuracao()
    logger = configurar_logging(config)
except ErroConfiguracao as erro:
    print(f"\nERRO DE CONFIGURAÇÃO: {erro}\nCorrija o arquivo e inicie o servidor novamente.\n", file=sys.stderr)
    raise SystemExit(1)

from core.repositorio import ErroPersistencia
from routers import backup, documentos, integridade, exportacoes

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


# 422: o FastAPI rejeitou a requisição (campo faltando, id fora do formato UUID, data inválida...).
# Só registra no log e devolve a resposta padrão do FastAPI.
@app.exception_handler(RequestValidationError)
async def tratar_dados_invalidos(request: Request, erro: RequestValidationError):
    campos = [".".join(str(parte) for parte in item["loc"]) for item in erro.errors()]
    logger.warning("DADOS_INVALIDOS status=422 metodo=%s rota=%s campos=%s", request.method, request.url.path, campos)
    return await request_validation_exception_handler(request, erro)


# 500: qualquer erro não previsto. O cliente recebe uma mensagem genérica e o detalhe fica no log.
@app.exception_handler(Exception)
def tratar_erro_inesperado(request: Request, erro: Exception):
    logger.error("ERRO_INESPERADO status=500 metodo=%s rota=%s erro=%r", request.method, request.url.path, erro)
    return JSONResponse(status_code=500, content={"detail": "Erro interno inesperado"})


@app.get("/")
def home():
    return{"mensagem":"Cofre de documentação em funcionamento"}
