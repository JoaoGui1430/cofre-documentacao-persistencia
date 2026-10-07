"""Persistência dos metadados em storage/metadata/documentos.json."""
import json
import os
import threading
from uuid import UUID

from pydantic import ValidationError

from app.documento import Documento
from core.armazenamento import diretorio

# Impede que duas requisições simultâneas leiam/escrevam o JSON ao mesmo tempo e uma apague a alteração da outra.
trava = threading.RLock()


class ErroPersistencia(Exception):
    """Falha ao ler ou gravar o arquivo de metadados."""


def _caminho_json():
    return diretorio("metadata") / "documentos.json"


def carregar_documentos() -> list[Documento]:
    caminho = _caminho_json()
    if not caminho.exists():
        return []  # primeira execução: ainda não há documentos

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, list):
            raise ErroPersistencia(f"{caminho.name} deveria conter uma lista de documentos")
        # model_validate converte cada dicionário do JSON em um objeto Documento (validando os campos).
        return [Documento.model_validate(item) for item in dados]
    except (OSError, UnicodeDecodeError) as erro:
        raise ErroPersistencia(f"Erro ao ler {caminho.name}: {erro}") from erro
    except json.JSONDecodeError as erro:
        raise ErroPersistencia(f"{caminho.name} contém JSON inválido: {erro}") from erro
    except ValidationError as erro:
        raise ErroPersistencia(f"{caminho.name} contém um registro inválido: {erro}") from erro


def salvar_documentos(documentos: list[Documento]):
    caminho = _caminho_json()
    temporario = caminho.with_name(caminho.name + ".tmp")
    # mode="json" converte UUID, datetime e date em texto para poderem ir para o JSON.
    dados = [doc.model_dump(mode="json") for doc in documentos]

    try:
        # Grava primeiro num arquivo temporário e depois troca pelo definitivo:
        # se o programa cair no meio da escrita, o documentos.json antigo continua intacto.
        with temporario.open("w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, caminho)
    except OSError as erro:
        raise ErroPersistencia(f"Erro ao gravar {caminho.name}: {erro}") from erro


def buscar_documento(id: UUID) -> Documento | None:
    for documento in carregar_documentos():
        if documento.id == id:
            return documento
    return None


def adicionar_documento(documento: Documento):
    with trava:
        documentos = carregar_documentos()
        documentos.append(documento)
        salvar_documentos(documentos)
