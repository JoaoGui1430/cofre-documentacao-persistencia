"""Operações sobre os arquivos físicos (os documentos originais)."""
import hashlib
from pathlib import Path

from core.config import BASE_DIR, carregar_configuracao


def diretorio(chave):
    """Retorna o diretório definido em config.yaml > diretorios > <chave>, criando-o se não existir."""
    config = carregar_configuracao()
    caminho = BASE_DIR / config["diretorios"][chave]
    caminho.mkdir(parents=True, exist_ok=True)
    return caminho


def caminho_arquivo(nome_armazenado) -> Path:
    return diretorio("arquivos") / nome_armazenado


def calcular_sha256(conteudo: bytes) -> str:
    # hashlib (biblioteca padrão) calcula o hash; hexdigest() devolve os 64 caracteres hexadecimais.
    return hashlib.sha256(conteudo).hexdigest()


def gravar_arquivo(nome_armazenado, conteudo: bytes) -> Path:
    caminho = caminho_arquivo(nome_armazenado)
    # Modo "xb": escrita binária que FALHA se o arquivo já existir, então nunca sobrescreve outro documento.
    with caminho.open("xb") as arquivo:
        arquivo.write(conteudo)
    return caminho


def remover_arquivo(nome_armazenado):
    caminho_arquivo(nome_armazenado).unlink(missing_ok=True)
