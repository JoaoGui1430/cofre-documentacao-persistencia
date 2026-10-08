import json
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED, BadZipFile
from pydantic import ValidationError
from fastapi import HTTPException

from app.documento import Documento
from utils.hash import calcular_hash_conteudo, calcular_sha256
from core import repositorio
from core.armazenamento import caminho_arquivo, diretorio, gravar_arquivo
from services import documentos_service as documentos


def gerar_destino(prefixo, formato):
    """Escolhe um nome livre na pasta de backups, ex.: backup_2026-10-08_1430.zip."""
    pasta = diretorio("backups")
    base = f"{prefixo}_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
    destino = pasta / f"{base}.{formato}"
    contador = 2
    # Dois backups no mesmo minuto ganham sufixo (_2, _3...) em vez de sobrescrever o anterior.
    while destino.exists():
        destino = pasta / f"{base}_{contador}.{formato}"
        contador += 1
    return destino


def criar_backup(projeto=None, versao=None):
    """Sem filtros: backup geral. Com projeto e/ou versão: backup seletivo só desses documentos."""
    seletivo = projeto is not None or versao is not None
    formato = documentos.config["backup"]["formato"]
    if formato != "zip":
        documentos.falhar(500, f"Formato de backup não suportado: {formato}", operacao="ERRO_BACKUP")

    # A trava impede que um upload/exclusão aconteça no meio do backup,
    # então o ZIP sempre reflete um estado consistente do cofre.
    with repositorio.trava:
        registros = documentos.listar_documentos(projeto=projeto, versao=versao)
        if seletivo and not registros:
            documentos.falhar(404, "Nenhum documento encontrado para os filtros informados", operacao="BACKUP_SELETIVO_VAZIO")

        destino = gerar_destino("backup_seletivo" if seletivo else "backup", formato)
        incluidos = []
        ausentes = []
        try:
            # zipfile (biblioteca padrão) cria o arquivo .zip; ZIP_DEFLATED ativa a compressão.
            # Modo "x" falha se o arquivo já existir: garantia extra de nunca sobrescrever.
            with ZipFile(destino, "x", compression=ZIP_DEFLATED) as pacote:
                for documento in registros:
                    caminho = caminho_arquivo(documento.nome_armazenado)
                    if not caminho.is_file():
                        # Um arquivo sumido não impede o backup dos demais; fica registrado no log e na resposta.
                        documentos.logger.warning("BACKUP_ARQUIVO_AUSENTE id=%s arquivo=%s", documento.id, documento.nome_armazenado)
                        ausentes.append(str(documento.id))
                        continue
                    hash_atual = calcular_sha256(caminho, documentos.config["hash"]["algoritmo"])
                    if hash_atual != documento.sha256:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Arquivo adulterado, backup adulterado: {documento.nome_original}",
                        )
                    pacote.write(caminho, f"documentos/{documento.nome_armazenado}")
                    incluidos.append(documento)

                # Metadados dos documentos incluídos, no mesmo formato do documentos.json do cofre.
                dados = [item.model_dump(mode="json") for item in incluidos]
                pacote.writestr("metadata/documentos.json", json.dumps(dados, ensure_ascii=False, indent=2))
        except HTTPException:
            documentos.limpar_parcial(destino)
            raise
        except (OSError, ValueError) as erro:
            documentos.limpar_parcial(destino)
            documentos.falhar(500, "Falha ao criar o backup compactado", erro, operacao="ERRO_BACKUP")

    documentos.logger.info(
        "BACKUP_CRIADO arquivo=%s documentos=%d seletivo=%s projeto=%s versao=%s",
        destino.name, len(incluidos), seletivo, projeto, versao,
    )
    return {
        "arquivo": destino.name,
        "tamanho": destino.stat().st_size,
        "tipo": "seletivo" if seletivo else "geral",
        "filtros": {"projeto": projeto, "versao": versao} if seletivo else None,
        "total_documentos": len(incluidos),
        "arquivos_ausentes": ausentes,
    }


def listar_backups():
    """Lê a pasta de backups e devolve nome e tamanho de cada ZIP, do mais antigo ao mais novo."""
    try:
        # glob("*.zip") lista só os arquivos .zip da pasta; st_mtime é a data em que cada um foi gravado.
        arquivos = sorted(diretorio("backups").glob("*.zip"), key=lambda caminho: caminho.stat().st_mtime)
        backups = [{"arquivo": caminho.name, "tamanho": caminho.stat().st_size} for caminho in arquivos]
    except OSError as erro:
        documentos.falhar(500, "Falha ao ler a pasta de backups", erro, operacao="ERRO_LEITURA")

    documentos.logger.info("LISTAGEM_BACKUPS total=%d", len(backups))
    return backups


def localizar_backup(nome):
    """Devolve o caminho do backup pedido, ou 404 se ele não existir."""
    pasta = diretorio("backups").resolve()
    caminho = (pasta / nome).resolve()
    # Só aceita um .zip que esteja diretamente na pasta de backups (bloqueia nomes como "../config.yaml").
    if caminho.parent != pasta or caminho.suffix != ".zip" or not caminho.is_file():
        documentos.falhar(404, f"Backup não encontrado: {nome}", operacao="BACKUP_NAO_ENCONTRADO")

    documentos.logger.info("DOWNLOAD_BACKUP arquivo=%s", caminho.name)
    return caminho

def restaurar_backup(nome):
    caminho = localizar_backup(nome)

    with repositorio.trava:
        if documentos.carregar_documentos():
            documentos.falhar(
                409,
                "A restauração só é permitida quando o cofre está vazio.",
                operacao="RESTAURACAO_COFRE_NAO_VAZIO",
            )

        try:
            with ZipFile(caminho, "r") as pacote:
                if pacote.testzip() is not None:
                    raise ValueError("O ZIP está corrompido.")

                nome_catalogo = "metadata/documentos.json"
                if nome_catalogo not in pacote.namelist():
                    raise ValueError("O backup não contém metadata/documentos.json.")

                dados = json.loads(pacote.read(nome_catalogo).decode("utf-8"))
                if not isinstance(dados, list):
                    raise ValueError("O catálogo do backup não é uma lista.")

                documentos_backup = [
                    Documento.model_validate(item)
                    for item in dados
                ]

                ids = [str(item.id) for item in documentos_backup]
                nomes = [item.nome_armazenado for item in documentos_backup]

                if len(ids) != len(set(ids)) or len(nomes) != len(set(nomes)):
                    raise ValueError("O catálogo do backup possui documentos duplicados.")

                arquivos = []
                membros_esperados = {nome_catalogo}

                for documento in documentos_backup:
                    nome = documento.nome_armazenado

                    if "/" in nome or "\\" in nome or Path(nome).name != nome:
                        raise ValueError("O backup contém um nome de arquivo inválido.")

                    membro = f"documentos/{nome}"
                    if membro not in pacote.namelist():
                        raise ValueError(f"Arquivo ausente no backup: {nome}")

                    conteudo = pacote.read(membro)

                    if len(conteudo) != documento.tamanho:
                        raise ValueError(f"Tamanho inválido no backup: {nome}")

                    hash_atual = calcular_hash_conteudo(
                        conteudo,
                        documentos.config["hash"]["algoritmo"],
                    )
                    if hash_atual != documento.sha256:
                        raise HTTPException(
                            status_code=409,
                            detail=f"Hash inválido no backup: {nome}",
                        )

                    arquivos.append((documento, conteudo))
                    membros_esperados.add(membro)

                if set(pacote.namelist()) != membros_esperados:
                    raise ValueError("O ZIP contém arquivos inesperados.")

        except HTTPException:
            raise
        except (BadZipFile, OSError, ValueError, KeyError, TypeError, ValidationError) as erro:
            documentos.falhar(
                400,
                "O backup é inválido ou não pôde ser lido.",
                erro,
                operacao="BACKUP_INVALIDO",
            )

        gravados = []

        try:
            for documento, conteudo in arquivos:
                destino = caminho_arquivo(documento.nome_armazenado)

                try:
                    gravar_arquivo(documento.nome_armazenado, conteudo)
                except FileExistsError:
                    raise
                except OSError:
                    documentos.limpar_parcial(destino)
                    raise

                gravados.append(documento.nome_armazenado)

            documentos.salvar_documentos(documentos_backup)

        except HTTPException:
            for nome_arquivo in gravados:
                documentos.limpar_parcial(caminho_arquivo(nome_arquivo))
            raise
        except OSError as erro:
            for nome_arquivo in gravados:
                documentos.limpar_parcial(caminho_arquivo(nome_arquivo))
            documentos.falhar(
                500,
                "Falha ao gravar os arquivos da restauração.",
                erro,
                operacao="ERRO_RESTAURACAO_BACKUP",
            )

    documentos.logger.info(
        "RESTAURACAO_BACKUP arquivo=%s documentos=%d",
        caminho.name,
        len(documentos_backup),
    )

    return {
        "backup": caminho.name,
        "documentos_restaurados": len(documentos_backup),
    }