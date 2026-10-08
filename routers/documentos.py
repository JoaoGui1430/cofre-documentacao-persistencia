import logging
import mimetypes
from datetime import date, datetime
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse

from app.documento import Documento, DocumentoAtualizacao
from core.armazenamento import caminho_arquivo, calcular_sha256, gravar_arquivo, remover_arquivo
from core.config import carregar_configuracao
from core.repositorio import ErroPersistencia, adicionar_documento, buscar_documento, carregar_documentos
from core.serializacao import operacao_armazenamento
from services import documentos_service as service
from services.estatisticas_service import calcular_estatisticas
from services.integridade_service import verificar_documento
router = APIRouter(prefix="/documentos", tags=["Documentos"])
logger = logging.getLogger("cofre_api")


def obter_documento_ou_404(id: UUID) -> Documento:
    documento = buscar_documento(id)
    if documento is None:
        logger.error("DOCUMENTO_NAO_ENCONTRADO id=%s", id)
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    return documento


# F1 - Upload
# Os metadados chegam como campos de formulário (Form) porque o arquivo é enviado
# em multipart/form-data; não dá para mandar um corpo JSON junto com o arquivo.
@router.post("", status_code=201, response_model=Documento)
@operacao_armazenamento()
def upload_documento(
    arquivo: UploadFile = File(...),
    categoria: str = Form(..., min_length=1),
    descricao: str = Form(""),
    projeto: str = Form(..., min_length=1),
    versao: str = Form(..., min_length=1),
    tipo_artefato: str = Form(..., min_length=1),
    responsavel: str = Form(..., min_length=1),
    data_versao: date = Form(...),
):
    # Path(...).name descarta qualquer pasta no nome enviado (ex.: "../../x.pdf" vira "x.pdf").
    nome_original = Path((arquivo.filename or "").replace("\\", "/")).name
    if not nome_original:
        logger.warning("UPLOAD_INVALIDO motivo=arquivo_sem_nome")
        raise HTTPException(status_code=400, detail="O arquivo enviado não tem nome")

    limite_bytes = carregar_configuracao()["upload"]["tamanho_maximo_mb"] * 1024 * 1024
    # Lê no máximo limite+1 bytes: se vier mais que o limite, sabemos que o arquivo é grande demais.
    conteudo = arquivo.file.read(limite_bytes + 1)
    if not conteudo:
        logger.warning("UPLOAD_INVALIDO motivo=arquivo_vazio arquivo=%s", nome_original)
        raise HTTPException(status_code=400, detail="O arquivo enviado está vazio")
    if len(conteudo) > limite_bytes:
        logger.warning("UPLOAD_INVALIDO motivo=tamanho_excedido arquivo=%s", nome_original)
        raise HTTPException(status_code=400, detail=f"O arquivo excede o limite de {limite_bytes // (1024 * 1024)} MB")

    id = uuid4()
    # Prefixar o id garante nomes únicos: dois "contrato.pdf" nunca se sobrescrevem.
    nome_armazenado = f"{id}_{nome_original}"
    # mimetypes (biblioteca padrão) deduz o tipo MIME pela extensão; se não souber, usa o que o cliente informou.
    tipo_mime = mimetypes.guess_type(nome_original)[0] or arquivo.content_type or "application/octet-stream"

    documento = Documento(
        id=id,
        nome_original=nome_original,
        nome_armazenado=nome_armazenado,
        extensao=Path(nome_original).suffix.lower(),  # com ponto, ex.: ".pdf"
        tipo_mime=tipo_mime,
        tamanho=len(conteudo),
        descricao=descricao,
        categoria=categoria,
        data_upload=datetime.now().replace(microsecond=0),
        sha256=calcular_sha256(conteudo),
        projeto=projeto,
        versao=versao,
        tipo_artefato=tipo_artefato,
        responsavel=responsavel,
        data_versao=data_versao,
    )

    try:
        gravar_arquivo(nome_armazenado, conteudo)
    except OSError as erro:
        logger.error("ERRO_ESCRITA arquivo=%s erro=%s", nome_armazenado, erro)
        raise HTTPException(status_code=500, detail="Erro ao gravar o arquivo no armazenamento")

    try:
        adicionar_documento(documento)
    except ErroPersistencia:
        # Os metadados não foram salvos: apaga o arquivo para não deixar um arquivo "órfão".
        remover_arquivo(nome_armazenado)
        raise

    logger.info("UPLOAD id=%s arquivo=%s tamanho=%d", id, nome_original, documento.tamanho)
    return documento


# F2 - Listagem (retorna os metadados completos de cada documento)
@router.get("", response_model=list[Documento])
def listar_documentos(categoria: str | None = None, projeto: str | None = None, versao: str | None = None):
    documentos = service.listar_documentos(categoria=categoria, projeto=projeto, versao=versao)
    logger.info("LISTAGEM total=%d categoria=%s projeto=%s versao=%s", len(documentos), categoria, projeto, versao)
    return documentos



#F16 - Recuperação de todos documentos de um projeto e versão
@router.get("/versao/download")
def baixar_versao(projeto: str = Query(...), versao: str = Query(...)):
    caminho = service.recuperar_versao(projeto, versao)
    return FileResponse(caminho, media_type="application/zip", filename=caminho.name) 

# F8 estatísticas
@router.get("/estatisticas")
def estatisticas():
    return calcular_estatisticas()

# F3 - Consulta
@router.get("/{id}", response_model=Documento)
def consultar_documento(id: UUID):
    documento = obter_documento_ou_404(id)
    logger.info("CONSULTA id=%s arquivo=%s", id, documento.nome_original)
    return documento


# F4 - Download
@router.get("/{id}/download")
def baixar_documento(id: UUID):
    documento = obter_documento_ou_404(id)
    caminho = caminho_arquivo(documento.nome_armazenado)
    if not caminho.is_file():
        logger.error("ARQUIVO_FISICO_NAO_ENCONTRADO id=%s arquivo=%s", id, documento.nome_armazenado)
        raise HTTPException(status_code=404, detail="Arquivo físico do documento não encontrado")

    logger.info("DOWNLOAD id=%s arquivo=%s", id, documento.nome_original)
    # FileResponse envia os bytes do arquivo exatamente como estão no disco;
    # filename= faz o navegador salvar com o nome original.
    return FileResponse(caminho, media_type=documento.tipo_mime, filename=documento.nome_original)

#F5 - Atualização metadados
@router.put("/{id}", response_model=Documento)
def atualizar_documento(id: UUID, atualizacao: DocumentoAtualizacao):
    return service.atualizar_documento(id, atualizacao)

#F6 - Exclusão
@router.delete("/{id}", status_code=204)
def excluir_documento(id: UUID):
    service.excluir_documento(id)
    return Response(status_code=204)

#F9 - Integridade individual
@router.get("/{id}/integridade")
def integridade_documento(id: UUID):
    return verificar_documento(id)
