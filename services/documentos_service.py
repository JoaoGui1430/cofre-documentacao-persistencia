import logging
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile, ZIP_DEFLATED  
import json

from fastapi import HTTPException
from pydantic import ValidationError

from app.documento import Documento
from core import repositorio
from core.armazenamento import diretorio, caminho_arquivo
from core.config import BASE_DIR, carregar_configuracao
from utils.hash import calcular_sha256

config = carregar_configuracao()
logger = logging.getLogger("cofre_api")
PASTA_ARQUIVOS = (BASE_DIR / config["diretorios"]["arquivos"]).resolve()
PASTA_EXPORTACOES = diretorio("exportacoes")
CATALOGO = BASE_DIR / config["diretorios"]["metadata"] / "documentos.json"

def falhar(status, mensagem, causa=None, operacao="REQUISICAO_INVALIDA"):
    """Registra o erro no log (no formato OPERACAO chave=valor) e devolve o erro HTTP ao cliente."""
    # 4xx = problema na requisição (WARNING); 5xx = falha do servidor (ERROR).
    nivel = logging.ERROR if status >= 500 else logging.WARNING
    if causa is None:
        logger.log(nivel, "%s status=%d detalhe=%s", operacao, status, mensagem)
    else:
        logger.log(nivel, "%s status=%d detalhe=%s causa=%s", operacao, status, mensagem, causa)
    raise HTTPException(status_code=status, detail=mensagem) from causa
def limpar_parcial(caminho):
    try:
        caminho.unlink(missing_ok=True)
    except OSError as erro:
        logger.error("ERRO_ESCRITA arquivo=%s detalhe=falha ao remover arquivo parcial erro=%s", caminho, erro)

def carregar_documentos():
    with repositorio.trava:
        try:
            return repositorio.carregar_documentos()
        except repositorio.ErroPersistencia as erro:
            falhar(500, "Não foi possivel ler o catálogo", erro, operacao="ERRO_LEITURA")

def salvar_documentos(documentos):
    with repositorio.trava:
        try:
            repositorio.salvar_documentos(documentos)
        except repositorio.ErroPersistencia as erro:
            falhar(500, "Não foi possivel salvar o catálogo", erro, operacao="ERRO_ESCRITA")

def normalizar_metadados(dados):
    resultado = {}
    for campo, valor in dados.items():
        if isinstance(valor, str):
            valor = valor.strip()
            if not valor and campo != "descricao":
                falhar(400, f"Campo obrigatório '{campo}' não informado")
        resultado[campo] = valor
    return resultado

def localizar(documentos, identificador):
    for documento in documentos:         
        if documento.id == identificador:
            return documento
    # O enunciado registra documento inexistente como ERROR (ex.: "ERROR DOCUMENTO_NAO_ENCONTRADO id=50").
    logger.error("DOCUMENTO_NAO_ENCONTRADO id=%s", identificador)
    raise HTTPException(status_code=404, detail=f"Documento {identificador} não encontrado")   

def buscar_documento(identificador):
    return localizar(carregar_documentos(), identificador)

def caminho_do_arquivo(documento):
    caminho = caminho_arquivo(documento.nome_armazenado).resolve()
    if caminho.parent != diretorio("arquivos").resolve():
        falhar(500, "Caminho do arquivo inválido", operacao="CAMINHO_INVALIDO")
    if not caminho.is_file():
        # O documento está no JSON mas o arquivo sumiu do disco: inconsistência do armazenamento (ERROR).
        logger.error("ARQUIVO_FISICO_NAO_ENCONTRADO id=%s arquivo=%s", documento.id, documento.nome_armazenado)
        raise HTTPException(status_code=404, detail=f"Arquivo não encontrado: {documento.id}")
    return caminho

def atualizar_documento(identificador, atualizacao):
    alteracoes = normalizar_metadados(atualizacao.model_dump(exclude_unset=True, exclude_none=True))
    with repositorio.trava:
        documentos = carregar_documentos()
        documento = localizar(documentos, identificador)
        if not alteracoes:
            falhar(400, "Nenhum campo para atualizar")
        dados = documento.model_dump()
        dados.update(alteracoes)
        try:
            atualizado = Documento.model_validate(dados)
        except ValidationError as erro:
            falhar(422, f"Dados inválidos: {erro}", operacao="DADOS_INVALIDOS")
        documentos = [atualizado if item.id == identificador else item for item in documentos]
        salvar_documentos(documentos)
        logger.info("ATUALIZACAO id=%s arquivo=%s campos=%s", identificador, documento.nome_original, list(alteracoes))
        return atualizado

def excluir_documento(identificador):
    with repositorio.trava:
        documentos = carregar_documentos()
        documento = localizar(documentos, identificador)
        caminho = caminho_do_arquivo(documento)
        temporario = caminho.with_name(caminho.name + ".tmp")
        catalogo_alterado = False
        try:
            caminho.replace(temporario)
            salvar_documentos([item for item in documentos if item.id != identificador])
            catalogo_alterado = True
            temporario.unlink()
        except (OSError, HTTPException) as erro:
            try:
                if temporario.exists():
                    temporario.replace(caminho)
                if catalogo_alterado:
                    salvar_documentos(documentos)
            except (OSError, HTTPException) as recuperacao:
               falhar(500, "Falha ao excluir o documento e recuperar o estado anterior", recuperacao, operacao="ERRO_EXCLUSAO")
            if isinstance(erro, HTTPException):
                raise
            falhar(500, "Falha ao excluir o documento", erro, operacao="ERRO_EXCLUSAO") 
                
    logger.info("EXCLUSAO id=%s arquivo=%s", identificador, documento.nome_original)

def listar_documentos(categoria=None, projeto=None, versao=None):
    filtros = normalizar_metadados({
        campo: valor
        for campo, valor in {"categoria": categoria, "projeto": projeto, "versao": versao}.items()
        if valor is not None
    })
    documentos = carregar_documentos()
    for campo, valor in filtros.items():
        documentos = [documento for documento in documentos if getattr(documento, campo) == valor]
    return documentos

def recuperar_versao(projeto, versao):
    with repositorio.trava:
        documentos = listar_documentos(projeto=projeto, versao=versao)
        if not documentos:
            falhar(404, f"Nenhum documento encontrado para projeto '{projeto}' e versão '{versao}'", operacao="RECUPERACAO_VERSAO_VAZIA")
        destino = PASTA_EXPORTACOES / f"release_{uuid4()}.zip"
        try:
            with ZipFile(destino, "x", compression=ZIP_DEFLATED) as pacote:
                for documento in documentos:
                    caminho = caminho_do_arquivo(documento)
                    if calcular_sha256(caminho, config["hash"]["algoritmo"]) != documento.sha256:
                        logger.warning("INTEGRIDADE_FALHOU id=%s arquivo=%s operacao=recuperacao_versao", documento.id, documento.nome_original)
                        raise HTTPException(status_code=409, detail=f"Falha na integridade do arquivo {documento.nome_original} (hash SHA256 não confere)")
                    nome = documento.nome_original.replace("\\", "/").rsplit("/", 1)[-1]
                    pacote.write(caminho, f"arquivos/{documento.id}/{nome}")
                dados = [item.model_dump(mode="json") for item in documentos]
                pacote.writestr("documentos.json", json.dumps(dados, ensure_ascii=False, indent= 2 ))
        except HTTPException:
            limpar_parcial(destino)
            raise
        except (OSError, ValueError) as erro:
            limpar_parcial(destino)
            falhar(500, "Falha ao criar o pacote ZIP", erro, operacao="ERRO_RECUPERACAO_VERSAO")
    logger.info("RECUPERACAO_VERSAO projeto=%s versao=%s documentos=%d arquivo=%s", projeto, versao, len(documentos), destino.name)
    return destino